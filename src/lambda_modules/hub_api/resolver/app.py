"""
Initialize the APIGatewayHttpResolver to be used throughout the API
"""

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from hub_api.resolver.serializer import custom_serializer
from hub_api.resolver.exception_handlers import (
    handle_unique_violation,
    handle_validation_error,
)
from hub_api.routes import (
    get_consumable,
    get_consumable_names,
    post_consumable,
    patch_consumable,
    get_department,
    get_job_title,
    get_job_title_titles,
    post_job_title,
    patch_job_title,
    get_service,
    get_service_slugs,
    post_service,
    patch_service,
)


app = APIGatewayHttpResolver(
    enable_validation=True,
    serializer=custom_serializer,
)

# Register custom exception handlers to the APIGatewayHttpResolver
app.exception_handler_manager.exception_handler(exc_class=handle_unique_violation)
app.exception_handler_manager.exception_handler(exc_class=handle_validation_error)

# Register routes
app.route("/department", "GET")(get_department)
app.route("/job-title", "GET")(get_job_title)
app.route("/job-title/titles", "GET")(get_job_title_titles)
app.route("/job-title", "POST")(post_job_title)
app.route("/job-title/<job_title_id>", "PATCH")(patch_job_title)
app.route("/consumable", "GET")(get_consumable)
app.route("/consumable/names", "GET")(get_consumable_names)
app.route("/consumable", "POST")(post_consumable)
app.route("/consumable/<consumable_id>", "PATCH")(patch_consumable)
app.route("/service", "GET")(get_service)
app.route("/service/slugs", "GET")(get_service_slugs)
app.route("/service", "POST")(post_service)
app.route("/service/<service_id>", "PATCH")(patch_service)
