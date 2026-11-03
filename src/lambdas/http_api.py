from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext
from hub_api.logger import logger
from hub_api.resolver import app
from hub_api.db import db_manager


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    loggable_event = {
        "routeKey": event.get("routeKey"),
        "rawPath": event.get("rawPath"),
        "rawQueryString": event.get("rawQueryString"),
        "queryStringParameters": event.get("queryStringParameters"),
        "requestContext": {
            "accountId": event["requestContext"].get("accountId"),
            "apiId": event["requestContext"].get("apiId"),
            "domainName": event["requestContext"].get("domainName"),
            "requestId": event["requestContext"].get("requestId"),
            "routeKey": event["requestContext"].get("routeKey"),
            "stage": event["requestContext"].get("stage"),
        },
        "body": event.get("body"),
    }
    logger.info("event: %s\n\ncontext: %s", loggable_event, context)

    response = app.resolve(event, context)

    # If Lambda is about to be destroyed, clean up
    if context.get_remaining_time_in_millis() < 100:
        db_manager.close_all()

    logger.info("response: %s", response)
    return response
