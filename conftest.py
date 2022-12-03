import pytest
import boto3
import subprocess
from types import SimpleNamespace

from moto import mock_s3, mock_sts
from gittf.settings import settings
from gittf.models import AWSCredentials
from gittf.adapters.plan_storage.s3 import S3PlanStorageClient

@pytest.fixture
def s3_client():
    with mock_s3():
        conn = boto3.client("s3")
        resp = conn.create_bucket(Bucket=settings.s3_plan_bucket_name)
        yield conn

@pytest.fixture
def sts_client():
    with mock_sts():
        conn = boto3.client("sts")
        yield conn
        
@pytest.fixture
def mock_github_check_run(requests_mock):
    requests_mock.post("https://api.github.com/repos/githaxs/test/check-runs", json={'id': 5})

@pytest.fixture
def mock_clone(monkeypatch):
    def mock_subprocess_run(cmd, shell, check, cwd=None, stdout=None, stderr=None, capture_output=False):
        print(cmd)
        return SimpleNamespace(stdout=b'foo')
    monkeypatch.setattr(subprocess, 'run', mock_subprocess_run)

@pytest.fixture
def storage_client():
    yield S3PlanStorageClient(AWSCredentials(
        aws_access_key_id="foo",
        aws_secret_access_key="bar"
    ), "foo")