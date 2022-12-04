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


    # DOCS: terraform version and use of tfenv
    def run(self, action):
        tf_version = self.project.terraform_version if self.project.terraform_version is not None else self.config.default_terraform_version
        workflow = Workflow.parse_obj(self.config.workflows.get(self.project.workflow, {}))
        env = self.create_env(tf_version)

        # TODO: implement drift detection
        assert action in ['plan', 'apply']
        if action == 'apply':
            self.plan_storage_client.get_project_plan(f"{self.project_path}/plan")  # this should download the plan

        conclusion, output = self._run_commands(workflow.get_commands(action), env)
        
        if action == 'plan' and conclusion == 'success':
            self.plan_storage_client.save_plan_and_lock(f"{self.project_path}/plan")

        return {
                "summary": f"{action.capitalize()} Output",
                "text": output,
                "conclusion":conclusion
            }

    def create_env(self, tf_version):
        path = os.environ['PATH']
        env = {
            'WORKSPACE': self.project.workspace or 'default',
            'PATH': path,
            'TFENV_ARCH': 'arm64',
            'TFENV_TERRAFORM_VERSION': tf_version
        }

        if settings.self_hosted is False:
            if self.config.roles.aws is not None:
                credentials = AWS.retrieve_assume_role_credentials(self.config.roles.aws, self.org)
                env['AWS_ACCESS_KEY_ID'] = credentials['AccessKeyId']
                env['AWS_SECRET_ACCESS_KEY'] = credentials['SecretAccessKey']
                env['AWS_SESSION_TOKEN'] = credentials['SessionToken']
        return env

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