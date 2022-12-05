import pytest
import os
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional

from gittf.adapters.ingress.run_worker import run_worker
from gittf.models import WorkerRequest, Config, Project, Roles

def create_jwt(data: dict, expires_minutes: Optional[int] = 5):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, 'foo', algorithm='HS256')
    return encoded_jwt
    
@pytest.mark.parametrize('mock_repo_location', [f'{os.path.dirname(os.path.abspath(__file__))}/demo'], indirect=True)
def test_api_returns_current_version(test_api):
    payload = create_jwt(WorkerRequest(
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
    ).dict())
    resp = test_api.post('/', json={'payload': payload})
    assert 'version' in resp.json()
