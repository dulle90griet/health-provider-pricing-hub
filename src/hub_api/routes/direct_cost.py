"""Provides method-specific routes for /direct-cost API routes."""

from typing_extensions import Annotated
from psycopg.sql import SQL, Identifier, Placeholder
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from hub_api.logger import logger
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql
from hub_api.models.requests import DirectCostLaxList, UpdateDirectCost


# @app.get("/direct-cost")
def get_direct_cost(
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """GET method for direct_cost table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)

    valid_search_columns = [
        "s.service_name",
        "c.consumable_name",
    ]
    search_sql = build_search_sql(
        queries.search_column,
        queries.search_string,
        valid_search_columns,
    )

    valid_sort_columns = [
        "service_id",
        "service",
        "consumable_id",
        "consumable",
        "cost_gbp",
    ]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("service", "consumable").to_sql()

    get_direct_cost_sql = SQL("""
        SELECT
            dc.service_id
            ,s.service_name AS service
            ,dc.consumable_id
            ,c.consumable_name AS consumable
            ,dc.cost_gbp
        FROM direct_cost dc
        LEFT OUTER JOIN service s
            ON dc.service_id = s.id
        LEFT OUTER JOIN consumable c
            ON dc.consumable_id = c.id
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
        cursor.execute(get_direct_cost_sql)
        results = cursor.fetchall()

    logger.info(results)
    return results


# @app.post("/direct-cost")
def post_direct_cost(body: Annotated[DirectCostLaxList, Body()]) -> None:
    """POST method for direct_cost table"""
    columns = ("service_id", "consumable_id", "cost_gbp")
    rows = body.root

    logger.info("POST into direct_cost values:")
    logger.info(rows)

    values = [
        row.model_dump()[column] if row.model_dump()[column] != "null" else None
        for column in columns
        for row in rows
    ]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO direct_cost ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


# @app.patch("/direct-cost/<service_id>/<consumable_id>")
def patch_direct_cost(
    service_id: str, consumable_id: str, body: Annotated[UpdateDirectCost, Body()]
) -> None:
    """PATCH method for direct_cost table"""
    logger.info(
        "PATCHing direct_cost with service ID %s and consumable ID %s",
        service_id,
        consumable_id,
    )
    logger.info(body)

    if "cost_gbp" not in body.model_fields_set:
        return None
    updated_cost = body.model_dump()["cost_gbp"]

    patch_direct_cost_sql = SQL("""
            UPDATE direct_cost
            SET cost_gbp = %s
            WHERE service_id = %s
                AND consumable_id = %s
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(
            patch_direct_cost_sql,
            [updated_cost, int(service_id), int(consumable_id)],
        )
