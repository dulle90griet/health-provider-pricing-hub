"""Provides method-specific routes for /service API routes."""

from typing_extensions import Annotated
from psycopg.sql import SQL, Identifier, Placeholder
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from hub_api.logger import logger
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql
from hub_api.models.requests import ServiceLaxList, UpdateService


# @app.get("/service")
def get_service(
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """GET method for service table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)

    valid_search_columns = [
        "pillar",
        "category",
        "service_name",
        "comments",
    ]
    search_sql = build_search_sql(
        queries.search_column, queries.search_string, valid_search_columns
    )

    valid_sort_columns = [
        "id",
        "pillar",
        "category",
        "service_name",
        "xero_code",
        "overhead_recovery_on_labour_percentage",
        "required_profit_margin_percentage",
        "acceptable_market_price_gbp",
        "our_current_unit_price_gbp",
        "new_unit_price_gbp",
        "new_day_rate_gbp",
        "comments",
    ]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("pillar", "category", "service_name").to_sql()

    get_sql = SQL("""
        SELECT *
        FROM service
        {search_clause}
        {sort_clause}
        LIMIT {per_page}
        OFFSET {offset}
    """).format(
        search_clause=search_sql,
        sort_clause=sort_clause_sql,
        per_page=per_page,
        offset=offset,
    )

    with DatabaseCursor() as cursor:
        cursor.execute(get_sql)
        results = cursor.fetchall()

    logger.info(results)
    return results


# @app.get("/service/slugs")
def get_service_slugs() -> list:
    """Method to GET all service slugs in the service table"""
    sort_clause_sql = SortClauses("category", "service_name").to_sql()
    get_service_slugs_sql = SQL("""
        SELECT
            id AS service_id
            ,category || ': ' || service_name AS service_slug
        FROM service
        {sort_clause}
    """).format(sort_clause=sort_clause_sql)

    with DatabaseCursor() as cursor:
        cursor.execute(get_service_slugs_sql)
        results = cursor.fetchall()

    return results


# @app.post("/service")
def post_service(body: Annotated[ServiceLaxList, Body()]) -> None:
    """POST method for service table"""
    columns = (
        "pillar",
        "category",
        "service_name",
        "xero_code",
        "overhead_recovery_on_labour_percentage",
        "required_profit_margin_percentage",
        "acceptable_market_price_gbp",
        "our_current_unit_price_gbp",
        "new_unit_price_gbp",
        "new_day_rate_gbp",
        "comments",
    )

    rows = body.root

    logger.info("POST into service values:")
    logger.info(rows)

    values = [
        row.model_dump()[column] if row.model_dump()[column] != "null" else None
        for column in columns
        for row in rows
    ]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO service ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


# @app.patch("/service/<service_id>")
def patch_service(service_id: int, body: Annotated[UpdateService, Body()]) -> None:
    """PATCH method for service table"""
    logger.info("PATCHing service ID: %s", service_id)
    logger.info(body)

    updated_columns = body.model_dump(exclude_unset=True)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("UPDATE service SET {} WHERE ID = %s").format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [int(service_id)])
