import boto3
from botocore.errorfactory import ClientError
import json

from gittf.settings import settings
from gittf.models import Lock
from gittf.logger import logger

class S3PlanStorageClient:
    def __init__(self, credentials, unique_identifier):
        self.client = boto3.client('s3',
            aws_access_key_id=credentials.aws_access_key_id,
            aws_secret_access_key=credentials.aws_secret_access_key)

        self.unique_identifier = unique_identifier

    def get_project_lock(self) -> Lock:
        try:
            logger.info(f"Retrieving lock from: {settings.s3_plan_bucket_name}/locks/{self.unique_identifier}")
            s3_object = self.client.get_object(
                Bucket=settings.s3_plan_bucket_name,
                Key=f"locks/{self.unique_identifier}"
            )

            body = s3_object['Body']
            return Lock(**json.loads(body.read()))
        except ClientError as e:
            logger.error(e)
            return None

    def save_plan_and_lock(self, plan_path, lock: Lock):
        logger.info(f"Saving plan and lock for: {self.unique_identifier}")
        self.client.put_object(
            Bucket=settings.s3_plan_bucket_name,
            Key=f"locks/{self.unique_identifier}",
            Body=json.dumps(lock.dict()).encode('utf-8')
        )

        self.client.upload_file(
            Filename=plan_path,
            Bucket=settings.s3_plan_bucket_name,
            Key=f"plans/{self.unique_identifier}"
        )

    def get_project_plan(self, plan_path):
        try:
            self.client.download_file(
                Bucket=settings.s3_plan_bucket_name,
                Key=f"plans/{self.unique_identifier}",
                Filename=plan_path
            )

            return True
        except ClientError as e:
            logger.error(e)
            return None

    def delete_plan_and_lock(self):
        self.client.delete_object(Bucket=settings.s3_plan_bucket_name, Key=f"locks/{self.unique_identifier}")
        self.client.delete_object(Bucket=settings.s3_plan_bucket_name, Key=f"plans/{self.unique_identifier}")