from gittf.settings import settings
from gittf.adapters.plans.s3 import S3PlanStorageClient
from gittf.models import PlanStorage

class PlanFactory:
    @staticmethod
    def get(plan_storage: PlanStorage):
        if plan_storage.aws is not None:
            if plan_storage.aws.s3 is not None:
                return S3PlanStorageClient(plan_storage.aws.s3)