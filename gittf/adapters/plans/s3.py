import boto3
from botocore.errorfactory import ClientError

from gittf.logger import logger
from gittf.models import S3Storage

class S3PlanStorageClient:
    def __init__(self, storage: S3Storage):
        self.client = boto3.client('s3',
            aws_access_key_id=storage.credentials.aws_access_key_id,
            aws_secret_access_key=storage.credentials.aws_secret_access_key)

        self.storage_details = storage

    def save(self, plan_path):
        logger.info(f"Saving plan for: {self.storage_details.path}")
        self.client.upload_file(
            Bucket=self.storage_details.bucket_name,
            Key=self.storage_details.path,
            Filename=plan_path
        )

    def get(self, plan_path):
        try:
            self.client.download_file(
                Bucket=self.storage_details.bucket_name,
                Key=self.storage_details.path,
                Filename=plan_path
            )

            return True
        except ClientError as e:
            logger.error(e)
            return None

    def delete(self):
        self.client.delete_object(
            Bucket=self.storage_details.bucket_name,
            Key=self.storage_details.path)