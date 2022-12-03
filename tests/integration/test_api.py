import os
from fastapi.testclient import TestClient

from gittf.api import app, run_worker
from gittf.models import WorkerRequest, Config, Project, Roles

# TODO: dynamically generate github application token, pull request, etc and make this a integration test
def test_github_request(sts_client, s3_client):
    # TODO: figure out how to auth between core and worker - JWT?
    response = run_worker(request=WorkerRequest(
        # TODO: remove this and mock the cloning method
        token=os.getenv("GITHUB_TOKEN"),
        pull_request_number=17,
        clone_url="foo",
        config=Config(version="v3", roles=Roles(aws="arn:aws:iam::000000000000:role/OrganizationAccountAccessRole")),
        project=Project(
            name="foo",
            dir=".",
            apply_requirements=[]),
        installation_id=5,
        plan_storage_credentials={
            'aws_access_key_id': 'foo',
            'aws_secret_access_key': 'bar',
        },
        repo='test',
        org='githaxs',
        branch='GabeL7r-patch-9',
        head_sha='9def3655742dd3aff5064adfb2b851e5ce5af6da',
        vcs='github',
        action='plan'
    ))

    assert 'conclusion' in response
    assert response['conclusion'] == 'failure'
