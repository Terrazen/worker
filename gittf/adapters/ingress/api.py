import jwt
from fastapi import FastAPI
from gittf.settings import settings
from gittf.models import WorkerRequest
from gittf.adapters.ingress.run_worker import run_worker

app = FastAPI()

@app.get('/health')
def health():
    return {
        "env": settings.env,
        "app_url": settings.app_url,
        "sha": settings.sha,
        "healthy": True      
    }

@app.post('/')
def worker_endpoint(token):
    decoded = jwt.decode(token, options={"verify_signature": False})
    request: WorkerRequest = WorkerRequest(**decoded)
    try:
        return {'version': settings.version}
    finally:
        run_worker(request)