import boto3
from gittf.logger import logger

# DOCS: Document how to create IAM policy to allow access
class AWS:
    @staticmethod
    def retrieve_assume_role_credentials(role, org):
        sts_client = boto3.client('sts')

        logger.info("Assuming client provided role.")
        external_assumed_role_object = sts_client.assume_role(
            RoleArn=role,
            RoleSessionName=f"GitTF",
            Tags=[
                # TODO: Generalize to other VCS Clients
                {
                    'Key': 'VCS',
                    'Value': 'GitHub'
                },
                {
                    'Key': 'VCS_ORG',
                    'Value': org
                }
            ]
        )

        return external_assumed_role_object['Credentials']