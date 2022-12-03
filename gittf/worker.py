from .logger import logger
import subprocess
import re
import os
from gittf.models import Lock, Project, Config
from gittf.workflow import Workflow
from gittf.logger import logger
from gittf.constants import SUPPORTED_TF_VERSIONS
from gittf.settings import settings
from gittf.adapters.clouds.aws import AWS


# TODO: call API for locks
# TODO: use provided credentials to download plans etc
class GitTFWorker:
    def __init__(self, repo_location, org, project: Project, config: Config, plan_storage_client):
        self.project = project
        self.config = config
        self.org = org
        self.project_path = f"{repo_location}/{self.project.dir}"
        self.task_name = f"GitTF/{self.project.name}"
        self.plan_storage_client = plan_storage_client


    def run(self, action):
        if self.project.terraform_version is not None:
            if self.project.terraform_version not in SUPPORTED_TF_VERSIONS:
                logger.error(f"Unsupported terraform version selected: {self.project.terraform_version}")
                return {
                    "summary": "Invalid Project TF Version.",
                    "text":f"Terraform version must be one of: {', '.join(SUPPORTED_TF_VERSIONS)}",
                    "conclusion": "failure"
                }
            else:
                logger.info(f"Selecting Terraform Version: {self.project.terraform_version}")
                subprocess.run(f"echo 'terraform {self.project.terraform_version}' > {self.project_path}/.tool-versions", shell=True, check=True, capture_output=True)

        else:
            if self.config.default_terraform_version not in SUPPORTED_TF_VERSIONS:
                logger.error(f"Unsupported terraform version selected: {self.config.default_terraform_version}")
                return {
                    "summary": "Invalid Default TF Version.",
                    "text":f"Terraform version must be one of: {', '.join(SUPPORTED_TF_VERSIONS)}",
                    "conclusion": "failure"
                }
            else:
                logger.info(f"Selecting Terraform Version: {self.config.default_terraform_version}")
                subprocess.run(f"echo 'terraform {self.config.default_terraform_version}' > {self.project_path}/.tool-versions", shell=True, check=True, capture_output=True)

        # Get the workflow for the project
        workflow = Workflow.parse_obj(self.config.workflows.get(self.project.workflow, {}))

        path = os.environ['PATH']
        env = {
            'WORKSPACE': self.project.workspace or 'default',
            'PATH': path
        }

        if settings.self_hosted is False:
            if self.config.roles.aws is not None:
                credentials = AWS.retrieve_assume_role_credentials(self.config.roles.aws, self.org)
                env['AWS_ACCESS_KEY_ID'] = credentials['AccessKeyId']
                env['AWS_SECRET_ACCESS_KEY'] = credentials['SecretAccessKey']
                env['AWS_SESSION_TOKEN'] = credentials['SessionToken']


        if action == 'plan':
            conclusion, output = self._run_commands(workflow.get_commands('plan'), env)

            lock = Lock(
                project=self.project,
                workflow=workflow
            )

            if conclusion == 'success':
                self.plan_storage_client.save_plan_and_lock(f"{self.project_path}/plan", lock)

            # TODO: figure out how to trim this if in CLI mode
            return {
                    "summary": "Plan Output",
                    "text":f"```diff\n{output}\n```",
                    "conclusion":conclusion
                }
        elif action == 'apply':

            self.plan_storage_client.get_project_plan(f"{self.project_path}/plan")  # this should download the plan
            conclusion, output = self._run_commands(workflow.get_commands('apply'), env)
            return {
                    "summary": "Apply Output",
                    "text":f"```diff\n{output}\n```",
                    "conclusion":conclusion
                }

        # TODO: implement drift detection
        elif action == 'drift_detection': #pragma: no cover
            pass
        
    # TODO: populate environment with variables from https://www.runatlantis.io/docs/custom-workflows.html
    def _run_commands(self, commands, env):
        output = None

        try:
            output = subprocess.run(
                commands,
                shell=True,
                env=env,
                cwd=f"{self.project_path}",
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            # We need to remove 2 leading whitespaces for GitHub diff
            # to render the plan correctly.
            output = output.stdout.decode("utf-8")
            result = '\n'.join([re.sub(r'^\s{2}', '', line) for line in output.split('\n')])
            logger.info(f"Commands output: {output}")
            return 'success', result
        except subprocess.CalledProcessError as e:
            logger.error("Command returned non-zero exit code.")
            logger.error(e.stdout.decode('utf-8'))
            return 'failure', e.stdout.decode('utf-8')