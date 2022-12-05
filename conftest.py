import os
import pytest
import boto3
import subprocess
from types import SimpleNamespace

from moto import mock_s3, mock_sts
from gittf.settings import settings
from gittf.models import AWSCredentials
from gittf.adapters.plans.s3 import S3PlanStorageClient
import gittf.adapters.ingress.run_worker as run_worker

@pytest.fixture
def s3_client():
    with mock_s3():
        conn = boto3.client("s3")
        resp = conn.create_bucket(Bucket="test")
        yield conn

@pytest.fixture
def sts_client():
    with mock_sts():
        conn = boto3.client("sts")
        yield conn
        
@pytest.fixture
def mock_github_check_run(requests_mock):
    requests_mock.post("https://api.github.com/repos/githaxs/test/check-runs", json={'id': 5})

@pytest.fixture(autouse=True)
def mock_clone(monkeypatch):
    def mock_clone(branch, clone_url, repo_location):
        print(clone_url)
        print(branch)
        return SimpleNamespace(stdout=b'foo')
    monkeypatch.setattr(run_worker, 'clone', mock_clone)

@pytest.fixture(autouse=True)
def repo_location(request, monkeypatch):
    def mock_clone():
        print(request.param)
        return request.param
    monkeypatch.setattr(run_worker, 'get_repo_location', mock_clone)
