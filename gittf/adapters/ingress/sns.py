
import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from gittf.models import WorkerRequest
from gittf.adapters.ingress.run_worker import run_worker


processor = BatchProcessor(event_type=EventType.SQS)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: SQSRecord):
    payload: str = record.body
    if payload:
        item: WorkerRequest = WorkerRequest(**json.loads(payload))
        run_worker(item)

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@batch_processor(record_handler=record_handler, processor=processor)
def lambda_handler(event, context: LambdaContext):
    return processor.response()