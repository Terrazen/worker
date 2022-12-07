import subprocess 
import requests
from datetime import datetime
from gittf.worker import GitTFWorker
from gittf.adapters.plans.factory import PlanFactory
from gittf.models import WorkerRequest, VCSStatus
from gittf.logger import logger
from gittf.settings import settings

def run_worker(request: WorkerRequest, jwt: str):
    print(request)
    plan_storage_client = PlanFactory.get(request.plan_storage)

    repo_location = get_repo_location()
    clone(request.branch, request.clone_url, repo_location)
    # TODO: retrieve plan before running worker
    worker = GitTFWorker(repo_location, request.project, request.config, request.env)
    result: VCSStatus = worker.run(request.action)

    logger.debug(result)

    if request.action == 'plan' and result.conclusion == 'success':
        plan_storage_client.save(f"{repo_location}/{request.project.dir}/plan")
    logger.debug(f"Making callback request to: {settings.gittf_api_url}/worker/callback")
    resp = requests.post(f"{settings.gittf_api_url}/worker/callback", headers={'X-GitTF-Token': jwt}, json=result.dict())

    try:
        resp.raise_for_status()
    except Exception as e:
        logger.error(e)

    return result

def clone(branch, clone_url, repo_location): # pragma: no cover
    subprocess.run(f"git clone --depth 1 --branch {branch} {clone_url} {repo_location}", shell=True, check=True)

def get_repo_location(): # pragma: no cover
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    return f"/tmp/{current_time}"