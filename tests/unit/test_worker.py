import os
import shutil
from gittf.worker import GitTFWorker
from gittf.models import Project, Config, Roles


def test_unsuccessful_plan(s3_client, sts_client):
    project = Project(
        name="foo",
        dir="."
    )

    config = Config(
        version="3",
        default_terraform_version="v1.2.9",
        roles=Roles(aws="arn:aws:iam::000000000000:role/OrganizationAccountAccessRole"))

    worker = GitTFWorker(".", project, config)
    result = worker.run("plan")

    assert result.conclusion == 'failure'
    assert 'Terraform initialized in an empty directory' in result.text

def test_successful_plan(s3_client, sts_client):
    dir = f"{os.path.dirname(os.path.abspath(__file__))}/test_terraform/"
    try:
        shutil.rmtree(f"{dir}/.terraform")
        os.remove(f"{dir}/terraform.tfstate")
        os.remove(f"{dir}/plan")
    except:
        pass
    project = Project(
        name="foo",
        dir=".",
        terraform_version="v1.1.9"
        # TODO: Add a new test to test selecting proper workspace
        #workspace="prod"
    )

    config = Config(
        version="3",
        default_terraform_version="v1.2.9",
        roles=Roles(aws="arn:aws:iam::000000000000:role/OrganizationAccountAccessRole"))

    worker = GitTFWorker(f"{os.path.dirname(os.path.abspath(__file__))}/test_terraform", project, config)
    result = worker.run("plan")

    assert result.conclusion == 'success'
    assert 'Terraform will perform the following actions' in result.text

    os.remove(f"{dir}/plan")

def test_unsuccessful_apply(sts_client):
    project = Project(
        name="foo",
        dir="."
    )

    config = Config(
        version="3",
        default_terraform_version="v1.2.9",
        roles=Roles(aws="arn:aws:iam::000000000000:role/OrganizationAccountAccessRole"))

    worker = GitTFWorker(".", project, config)
    result = worker.run("apply")

    assert result.conclusion == 'failure'
    assert 'Failed to load "plan"' in result.text