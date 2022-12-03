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
# TODO: add in actions?
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

    apply_errors = vcs.apply_requirements_met(request.project.apply_requirements)
    if len(apply_errors) > 0:
        # For errors, we want to give the user the errors and their original plan back
        logger.info("Apply requirements are not met")
        user_readable_errors = '\n* '.join(apply_errors)
        return vcs.comment(
            comment=f"""
### Apply requirements ({','.join(request.project.apply_requirements)}) are not met
* {user_readable_errors}
            """
        )

    # Create initial status 
    logger.info("Creating initial Check Run")
    status_id = vcs.create_status(
        name=f"Project: {request.project.name} Workspace: {request.project.workspace}",
        head_sha=request.head_sha,
    )

    # Clone Repo
    # TODO: if clone fails update status
    repo_location = vcs.clone()

    unique_identifier = f"{request.org}/{request.repo}/{request.pull_request_number}/{request.project.name}"
    plan_storage_client = S3PlanStorageClient(request.plan_storage_credentials, unique_identifier)

    worker = GitTFWorker(repo_location, request.org, request.project, request.config, plan_storage_client)
    result = worker.run(request.action)

    logger.debug(result)
    vcs.update_status(
        id=status_id,
        conclusion = result['conclusion'],
        summary=result['summary'],
        text=result['text']
    )

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
