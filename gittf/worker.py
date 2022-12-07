from .logger import logger
import subprocess
import re
import os
from gittf.models import Project, Config, VCSStatus
from gittf.workflow import Workflow
from gittf.logger import logger
from gittf.settings import settings


class GitTFWorker:
    def __init__(self, repo_location, project: Project, config: Config, env: dict = {}):
        self.repo_location = repo_location
        self.project = project
        self.config = config
        self.env = env
        self.project_path = f"{self.repo_location}/{self.project.dir}"

    # DOCS: terraform version and use of tfenv
    def run(self, action) -> VCSStatus:
        tf_version = self.project.terraform_version if self.project.terraform_version is not None else self.config.default_terraform_version
        workflow = Workflow.parse_obj(self.config.workflows.get(self.project.workflow, {}))
        env = self.create_env(tf_version)

        # TODO: implement drift detection
        assert action in ['plan', 'apply']

        conclusion, output = self._run_commands(workflow.get_commands(action), env)
        
        return VCSStatus(
            title=f"{action.capitalize()} Output",
            text=output,
            summary="",
            conclusion=conclusion,
            )

    def create_env(self, tf_version):
        path = os.environ['PATH']
        env = {
            'WORKSPACE': self.project.workspace or 'default',
            'PATH': path,
            'TFENV_ARCH': 'arm64',
            'TFENV_TERRAFORM_VERSION': tf_version,
            **self.env
        }

        return env

    # TODO: populate environment with variables from https://www.runatlantis.io/docs/custom-workflows.html
    def _run_commands(self, commands, env):
        output = None

        try:
            process_output = subprocess.run(
                commands,
                shell=True,
                env=env,
                cwd=f"{self.project_path}",
                #check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            output = process_output.stdout.decode("utf-8")
            result = '\n'.join([re.sub(r'^\s{2}', '', line) for line in output.split('\n')])
            logger.info(f"Commands output: {output}")
            logger.info(f'Return code: {process_output.returncode}')
 
            # TODO: the process is returning a zero exit code if there is a command that succeeds after
            # the plan. How do we capture the terraform plan exit code and then return the exit code
            if process_output.returncode == 2 and 'terraform plan -detailed-exitcode' in commands:
                return 'neutral', result
            
            if process_output.returncode != 0:
                raise subprocess.CalledProcessError
            # We need to remove 2 leading whitespaces for GitHub diff
            # to render the plan correctly.
            return 'success', result
            # TODO: test this reports back to GitHub
        except subprocess.CalledProcessError as e:
            logger.error("Command returned non-zero exit code.")
            logger.error(process_output.stdout.decode('utf-8'))
            return 'failure', process_output.stdout.decode('utf-8')