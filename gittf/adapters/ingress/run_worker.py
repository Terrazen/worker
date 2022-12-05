import subprocess 
from datetime import datetime
from gittf.worker import GitTFWorker
from gittf.adapters.plans.factory import PlanFactory
from gittf.models import WorkerRequest
from gittf.logger import logger

def run_worker(request: WorkerRequest):
    plan_storage_client = PlanFactory.get(request.plan_storage)

    repo_location = get_repo_location()
    clone(request.branch, request.clone_url, repo_location)
    # TODO: retrieve plan before running worker
    worker = GitTFWorker(repo_location, request.project, request.config)
    result = worker.run(request.action)

    logger.debug(result)

    if request.action == 'plan' and result.conclusion == 'success':
        plan_storage_client.save(f"{repo_location}/{request.project.dir}/plan")
    #gittf.finish(result)
    return result

def clone(branch, clone_url, repo_location): # pragma: no cover
    subprocess.run(f"git clone --depth 1 --branch {branch} {clone_url} {repo_location}", shell=True, check=True)

def get_repo_location(): # pragma: no cover
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    return f"/tmp/{current_time}"