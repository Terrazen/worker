import pytest
import boto3
from types import SimpleNamespace

from moto import mock_s3
import gittf.adapters.ingress.run_worker as run_worker
from gittf.adapters.ingress.api import app
from fastapi.testclient import TestClient

@pytest.fixture
def test_api():
    yield TestClient(app)


@pytest.fixture
def s3_client():
    with mock_s3():
        conn = boto3.client("s3")
        resp = conn.create_bucket(Bucket="test")
        yield conn

@pytest.fixture(autouse=True)
def mock_clone(monkeypatch):
    def clone(branch, clone_url, repo_location):
        print(clone_url)
        print(branch)
        return SimpleNamespace(stdout=b'foo')
    monkeypatch.setattr(run_worker, 'clone', clone)

@pytest.fixture(autouse=True)
def mock_repo_location(request, monkeypatch):
    def mock_repo_location():
        print(request.param)
        return request.param
    monkeypatch.setattr(run_worker, 'get_repo_location', mock_repo_location)
