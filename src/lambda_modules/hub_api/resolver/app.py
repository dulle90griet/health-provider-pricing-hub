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
    get_client,
    get_client_names,
    post_client,
    patch_client,
    get_consumable,
    get_consumable_names,
    post_consumable,
    patch_consumable,
    get_department,
    get_direct_cost,
    post_direct_cost,
    patch_direct_cost,
    get_job_title,
    get_job_title_titles,
    post_job_title,
    patch_job_title,
    get_labour_cost,
    post_labour_cost,
    patch_labour_cost,
    get_overhead_cost,
    post_overhead_cost,
    patch_overhead_cost,
    get_service,
    get_service_slugs,
    post_service,
    patch_service,
    get_tender,
    get_tender_single,
    get_tender_titles,
    post_tender,
    patch_tender,
    get_tender_line_items,
    post_tender_line_items,
    patch_tender_line_item,
)


app = APIGatewayHttpResolver(
    enable_validation=True,
    serializer=custom_serializer,
)

# Register custom exception handlers to the APIGatewayHttpResolver
app.exception_handler_manager.exception_handler(exc_class=handle_unique_violation)
app.exception_handler_manager.exception_handler(exc_class=handle_validation_error)

# Register routes
app.route("/client", "GET")(get_client)
app.route("/client/names", "GET")(get_client_names)
app.route("/client", "POST")(post_client)
app.route("/client/<client_id>", "PATCH")(patch_client)
app.route("/consumable", "GET")(get_consumable)
app.route("/consumable/names", "GET")(get_consumable_names)
app.route("/consumable", "POST")(post_consumable)
app.route("/consumable/<consumable_id>", "PATCH")(patch_consumable)
app.route("/department", "GET")(get_department)
app.route("/direct-cost", "GET")(get_direct_cost)
app.route("/direct-cost", "POST")(post_direct_cost)
app.route("/direct-cost/<service_id>/<consumable_id>", "PATCH")(patch_direct_cost)
app.route("/job-title", "GET")(get_job_title)
app.route("/job-title/titles", "GET")(get_job_title_titles)
app.route("/job-title", "POST")(post_job_title)
app.route("/job-title/<job_title_id>", "PATCH")(patch_job_title)
app.route("/labour-cost", "GET")(get_labour_cost)
app.route("/labour-cost", "POST")(post_labour_cost)
app.route("/labour-cost/<service_id>/<title_engaged_id>", "PATCH")(patch_labour_cost)
app.route("/overhead-cost", "GET")(get_overhead_cost)
app.route("/overhead-cost", "POST")(post_overhead_cost)
app.route("/overhead-cost/<overhead_cost_id>", "PATCH")(patch_overhead_cost)
app.route("/service", "GET")(get_service)
app.route("/service/slugs", "GET")(get_service_slugs)
app.route("/service", "POST")(post_service)
app.route("/service/<service_id>", "PATCH")(patch_service)
app.route("/tender", "GET")(get_tender)
app.route("/tender/single/<tender_id>", "GET")(get_tender_single)
app.route("/tender/titles", "GET")(get_tender_titles)
app.route("/tender", "POST")(post_tender)
app.route("/tender/<tender_id>", "PATCH")(patch_tender)
app.route("/tender/line-items/<tender_id>", "GET")(get_tender_line_items)
app.route("/tender/line-items", "POST")(post_tender_line_items)
app.route("/tender/line-items/<tender_id>/<service_id>", "PATCH")(
    patch_tender_line_item
)
