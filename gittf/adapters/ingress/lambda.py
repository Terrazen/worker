import rollbar
from mangum import Mangum
from gittf.adapters.ingress.api import app

@rollbar.lambda_function
def handler(event, context):  # pragma: no cover
    try:
        asgi_handler = Mangum(app)
        # Call the instance with the event arguments
        response = asgi_handler(event, context)

        return response
    except BaseException:
        rollbar.report_exc_info()
        rollbar.wait()
        raise