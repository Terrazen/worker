import os
import shutil
from gittf.worker import GitTFWorker
from gittf.models import Project, Config, Lock, Roles


def test_unsupported_project_terraform_version():
    project = Project(
        name="foo",
        dir=".",
        terraform_version="v0.0.0"
    )
    config = Config(
        version="3",
        roles=Roles(aws="foo"))

    worker = GitTFWorker(".", "foo", project, config, plan_storage_client=None)

    result =  worker.run("apply")

    assert result['conclusion'] == 'failure'
    assert 'Invalid Project TF Version' in result['summary']

def test_unsupported_default_terraform_version():
    project = Project(
        name="foo",
        dir="."
    )
    config = Config(
        version="3",
        default_terraform_version="v0.0.0",
        roles=Roles(aws="foo"))

    worker = GitTFWorker(".", "foo", project, config, plan_storage_client=None)

    result =  worker.run("apply")

    assert result['conclusion'] == 'failure'
    assert 'Invalid Default TF Version' in result['summary']

def test_unsuccessful_plan(s3_client, sts_client, storage_client):
    project = Project(
        name="foo",
        dir="."
    )

    config = Config(
        version="3",
        default_terraform_version="v1.2.9",
        roles=Roles(aws="arn:aws:iam::000000000000:role/OrganizationAccountAccessRole"))

    worker = GitTFWorker(".", "foo", project, config, storage_client)
    result = worker.run("plan")

    assert result['conclusion'] == 'failure'
    assert 'Terraform initialized in an empty directory' in result['text']

def test_successful_plan(s3_client, sts_client, storage_client):
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

    worker = GitTFWorker(f"{os.path.dirname(os.path.abspath(__file__))}/test_terraform", "foo", project, config, storage_client)
    result = worker.run("plan")

    assert result['conclusion'] == 'success'
    assert 'Terraform will perform the following actions' in result['text']

    os.remove(f"{dir}/plan")

    result = worker.run("apply")
    assert 'Apply complete' in result['text']


def test_unsuccessful_apply(storage_client, sts_client):
    project = Project(
        name="foo",
        dir="."
    )

    config = Config(
        version="3",
        default_terraform_version="v1.2.9",
        roles=Roles(aws="arn:aws:iam::000000000000:role/OrganizationAccountAccessRole"))

    worker = GitTFWorker(".", "foo", project, config, storage_client)
    result = worker.run("apply")

    assert result['conclusion'] == 'failure'
    assert 'Failed to load "plan"' in result['text']


def test_unlock(s3_client, storage_client):
    project = Project(
        name="foo",
        dir="."
    )
    config = Config(
        version="3",
        default_terraform_version="v1.2.9",
        roles=Roles(aws="foo"))


    worker = GitTFWorker(".", "foo", project, config, storage_client)
    client = storage_client

    lock = Lock(
        project=Project(name="foo", dir="."),
        workflow={}
    )
    client.save_plan_and_lock(
        f"{os.path.dirname(os.path.abspath(__file__))}/test_plan",
        lock
    )

    retrieved_lock = client.get_project_lock()

    assert retrieved_lock.project.name == 'foo'

    worker.run("unlock")

    retrieved_lock = client.get_project_lock()
    assert retrieved_lock is None

    assert client.get_project_plan(".") is None