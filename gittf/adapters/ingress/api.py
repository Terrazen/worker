import os
from fastapi import FastAPI
from gittf.settings import settings
from gittf.worker import GitTFWorker
from gittf.models import WorkerRequest
from gittf.logger import logger
from gittf.adapters.vcs.github import GitHubVCS
from gittf.adapters.plan_storage.s3 import S3PlanStorageClient

import rollbar
from mangum import Mangum

app = FastAPI()

@app.get('/health')
def health():
    return {
        "env": settings.env,
        "app_url": settings.app_url,
        "sha": settings.sha,
        "healthy": True      
    }

# TODO: determine how to store plans in hosted or clients account
# TODO: this receives a token that needs to be decoded
@app.post('/')
def worker_endpoint(request: WorkerRequest):
    try:
        return {'message': 'processing request'}
    finally:
        run_worker(request)

def run_worker(request: WorkerRequest):
    vcs = None

    if request.vcs == 'github':
        vcs = GitHubVCS(
            token=request.token,
            org=request.org,
            repo=request.repo,
            branch=request.branch,
            number=request.pull_request_number
        )

    # Clone Repo
    try:
        repo_location = vcs.clone()
    except Exception as e:
        return logger.error(e)
        # TODO: send failed status

    plan_storage_client = S3PlanStorageClient(request.plan_storage_credentials, unique_identifier)

    worker = GitTFWorker(repo_location, request.org, request.project, request.config, plan_storage_client)
    result = worker.run(request.action)

    logger.debug(result)

    # TODO: make request to api status with result and jwt
    return result


@rollbar.lambda_function
def handler(event, context):  # pragma: no cover
    try:
        asgi_handler = Mangum(app)
        # Call the instance with the event arguments
        response = asgi_handler(event, context)

        return response
    except BaseException:
        rollbar.report_exc_info()
        rollbar.wait()
        raise
