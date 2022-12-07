import jwt
import threading
from fastapi import FastAPI
from gittf.settings import settings
from gittf.models import WorkerRequest, WorkerAPIRequest
from gittf.adapters.ingress.run_worker import run_worker

app = FastAPI()

@app.get('/health')
def health(): # pragma: no cover
    return {
        "app_url": settings.gittf_api_url,
        "healthy": True,
        "version": settings.version
    }

@app.post('/')
async def worker_endpoint(req: WorkerAPIRequest):
    decoded = jwt.decode(req.payload, options={"verify_signature": False}, algorithms='HS256')
    request: WorkerRequest = WorkerRequest(**decoded)

    def thread():
        run_worker(request, req.payload)
    threading.Thread(target=thread).start()
    return {'message': 'payload received'}
