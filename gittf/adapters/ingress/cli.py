import os
import click
import yaml
from gittf.settings import settings
from gittf.worker import GitTFWorker
from gittf.models import Config
from gittf.logger import logger

@click.group()
def main():
    pass

@main.command()
@click.option('-p', '--project', required=True)
@click.option('-a', '--action', type=click.Choice(["plan", "apply"]), required=True)
def git_tf(project, action):
    config = get_configuration(os.getcwd())

    selected_project = None

    for p in config.projects:
        if project == p.name:
            selected_project = p
            break 

    if selected_project is None:
        return print(f"Could not find project with name {project}")


    worker = GitTFWorker(os.getcwd(), "", selected_project, config)
    result = worker.run(action)

    print(result['text'])


def get_configuration(repo_location):
    found_config = False
    loaded_config = None

    for config_file_path in settings.config_files:
        logger.debug(f"Looking for {config_file_path} in {repo_location}")
        if os.path.exists(f"{repo_location}/{config_file_path}"):
            logger.debug(f"Found config file at: {repo_location}/{config_file_path}")
            found_config = True
            break

    if found_config is False:
        raise Exception("Could not find config file")

    with open(f"{repo_location}/{config_file_path}") as stream:
        loaded_config = yaml.safe_load(stream)
        logger.debug(f"Loaded: {loaded_config}")

    config = Config(**loaded_config)
    return config