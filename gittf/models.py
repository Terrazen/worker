# DOCS: Document the difference between GitTF and Atlantis
# DOCS: Document each of the following fields and what they mean
from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime

class Autoplan(BaseModel):
    enabled: Optional[bool] = True
    when_modified: Optional[List[str]] = ["**/*.tf*"]

class Project(BaseModel):
    name: str
    dir: str
    workspace: Optional[str] = "default"
    execution_order_group: Optional[int] = 0
    delete_source_branch_on_merge: Optional[bool] = False
    autoplan: Optional[Autoplan]
    terraform_version: Optional[str]
    apply_requirements: Optional[List[str]] = []
    workflow: Optional[str] = ""

class Roles(BaseModel):
    aws: Optional[str] = None
    gcp: Optional[str] = None

class Hosting(BaseModel):
    self: bool = False
    worker_url: Optional[str] = None

class Config(BaseModel):
    version: str
    automerge: Optional[bool] = False
    delete_source_branch_on_merge: Optional[bool] = False
    projects: Optional[List[Project]] = []
    workflows: Optional[dict] = {}
    allowed_regexp_prefixes: Optional[List[str]] = []
    # The below differ from Atlantis
    default_terraform_version: Optional[str] = "v1.2.9"
    roles: Optional[Roles] = Roles()
    hosting: Optional[Hosting]

class Lock(BaseModel):
    project: Project
    workflow: Optional[dict] = {}
    start_at: str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


class ActionEnum(str, Enum):
    apply = 'apply'
    plan = 'plan'
    unlock = 'unlock'
    drift_detection = 'drift_detection'

class VCSEnum(str, Enum):
    github = 'github'

class AWSCredentials(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str

class S3Storage(BaseModel):
    path: str

class AWSStorage(BaseModel):
    s3: Optional[S3Storage]
    credentials: AWSCredentials

class PlanStorage(BaseModel):
    aws: Optional[AWSStorage]


class WorkerRequest(BaseModel):
    token: str
    pull_request_number: str
    config: Config
    project: Project
    installation_id: str
    repo: str
    org: str
    branch: str
    head_sha: str
    vcs: VCSEnum
    action: ActionEnum
    check_run_id: str
    plan_storage: Optional[PlanStorage] # If not provided it will use the credentials of the worker

class Conclusion(str, Enum):
    action_required = 'action_required'
    cancelled = 'cancelled'
    failure = 'failure'
    neutral = 'neutral'
    success = 'success'
    skipped = 'skipped'
    stale = 'stale'
    timed_out = 'timed_out'

class VCSStatus(BaseModel):
    title: str
    summary: str
    text: str
    conclusion: Conclusion

class VCSInProgressStatus(BaseModel):
    pass

class VCSCompletedStatus(BaseModel):
    pass