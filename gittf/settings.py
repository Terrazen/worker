import os
from pydantic import BaseSettings, Field
from typing import List

class Settings(BaseSettings):
    vcs: str = Field("github", env='VCS')
    vcs_token: str = Field(None, env='VCS_TOKEN')
    webhook_secret: str = Field("", env='WEBHOOK_SECRET')
    mode: str = Field("api", env='MODE')
    sentry_dsn: str = Field(None, env='SENTRY_DSN')
    rollbar_dsn: str = Field(None, env='ROLLBAR_DSN')
    terraform_version: str = Field(None, env='TERRAFORM_VERSION')

    # GitTF Settings
    gittf_api_url: str = Field(..., env='GITTF_API_URL')
    version: str = Field(..., env='GITTF_VERSION')
    self_hosted: bool = Field(True, env='SELF_HOSTED')
    config_files: List[str] = ["gittf.yaml", "atlantis.yaml", "atlantis.yml"]

    class Config:
        env_file = '.test.env' if os.getenv('ENV') != 'prod' else '.env'
        env_file_encoding = 'utf-8'

settings = Settings()