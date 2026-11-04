"""Custom exception handlers for the APIGatewayHTTPResolver"""

import json
from http import HTTPStatus
from psycopg.errors import UniqueViolation
from aws_lambda_powertools.event_handler import Response, content_types
from hub_api.exceptions import InvalidParameterError


# @app.exception_handler(InvalidParameterError)
def handle_validation_error(exp: InvalidParameterError):
    return Response(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content_type=content_types.APPLICATION_JSON,
        body={
            "statusCode": HTTPStatus.UNPROCESSABLE_ENTITY,
            "detail": {
                # "loc": exp.loc,
                "message": exp.msg,
            },
        },
    )


# @app.exception_handler(UniqueViolation)
def handle_unique_violation(exp: UniqueViolation):
    constraint = exp.diag.constraint_name or "unique constraint"
    detail = exp.diag.message_detail

    return Response(
        status_code=409,
        content_type=content_types.APPLICATION_JSON,
        body=json.dumps(
            {
                "statusCode": HTTPStatus.CONFLICT,
                "detail": [
                    {
                        "loc": ["body", constraint],
                        "type": "unique_violation",
                        "message": f"Duplicate value violates unique constraint '{constraint}'. {detail}",
                    }
                ],
            }
        ),
    )
