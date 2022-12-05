import pytest
import os

from gittf.adapters.ingress.run_worker import run_worker
from gittf.models import WorkerRequest, Config, Project, Roles, AWSStorage, S3Storage

@pytest.mark.parametrize('repo_location', [f'{os.path.dirname(os.path.abspath(__file__))}/demo'], indirect=True)
def test_github_request(sts_client, s3_client):
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
        plan_storage={
            'aws': {
                's3': {
                    'path': 'foo',
                    'bucket_name': 'foo',
                    'credentials': {
                        'aws_access_key_id': 'foo',
                        'aws_secret_access_key': 'bar'
                    }
                }
            }
        },
        repo='test',
        org='githaxs',
        branch='GabeL7r-patch-9',
        head_sha='9def3655742dd3aff5064adfb2b851e5ce5af6da',
        vcs='github',
        check_run_id=4,
        action='plan'
    ))

    assert response.conclusion == 'failure'

#def test_api_returns_current_version():
#    assert True is False

#def test_api_handles_jwt_request():
#    assert True is False