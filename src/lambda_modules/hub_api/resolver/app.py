"""
Initialize the APIGatewayHttpResolver to be used throughout the API
"""

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from hub_api.resolver.serializer import custom_serializer
from hub_api.resolver.exception_handlers import (
    handle_unique_violation,
    handle_validation_error,
)


app = APIGatewayHttpResolver(
    enable_validation=True,
    serializer=custom_serializer,
)

# Register custom exception handlers to the APIGatewayHttpResolver
app.exception_handler_manager.exception_handler(exc_class=handle_unique_violation)
app.exception_handler_manager.exception_handler(exc_class=handle_validation_error)
