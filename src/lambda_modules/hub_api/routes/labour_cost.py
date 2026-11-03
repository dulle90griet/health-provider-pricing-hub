"""Provides method-specific routes for /labour-cost API routes."""

from typing_extensions import Annotated
from psycopg.sql import SQL, Identifier, Placeholder
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from hub_api.logger import logger
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql
from hub_api.models.requests import LabourCostLaxList, UpdateLabourCost


# @app.get("/labour-cost")
def get_labour_cost(
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """GET method for labour_cost table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)

    valid_search_columns = [
        "s.service_name",
        "jt.title",
    ]
    search_sql = build_search_sql(
        queries.search_column,
        queries.search_string,
        valid_search_columns,
    )

    valid_sort_columns = [
        "service_id",
        "service",
        "title_engaged_id",
        "title_engaged",
        "required_time_mins",
    ]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("service", "title_engaged").to_sql()

    get_labour_cost_sql = SQL("""
        SELECT
            lc.service_id
            ,s.service_name AS service
            ,lc.title_engaged_id
            ,jt.title AS title_engaged
            ,lc.required_time_mins
        FROM labour_cost lc
        LEFT OUTER JOIN service s
            ON lc.service_id = s.id
        LEFT OUTER JOIN job_title jt
            ON lc.title_engaged_id = jt.id
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
        cursor.execute(get_labour_cost_sql)
        results = cursor.fetchall()

    logger.info(results)
    return results


# @app.post("/labour-cost")
def post_labour_cost(body: Annotated[LabourCostLaxList, Body()]) -> None:
    """POST method for labour_cost table"""
    columns = ("service_id", "title_engaged_id", "required_time_mins")
    rows = body.root

    logger.info("POST into labour_cost values:")
    logger.info(rows)

    values = [
        row.model_dump()[column] if row.model_dump()[column] != "null" else None
        for column in columns
        for row in rows
    ]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO labour_cost ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


# @app.patch("/labour-cost/<service_id>/<title_engaged_id>")
def patch_labour_cost(
    service_id: str, title_engaged_id: str, body: Annotated[UpdateLabourCost, Body()]
) -> None:
    """PATCH method for labour_cost table"""
    logger.info(
        "PATCHing labour_cost with service ID %s and job title ID %s",
        service_id,
        title_engaged_id,
    )
    logger.info(body)

    if "required_time_mins" not in body.model_fields_set:
        return None
    updated_required_time = body.model_dump()["required_time_mins"]

    patch_labour_cost_sql = SQL("""
            UPDATE labour_cost
            SET required_time_mins = %s
            WHERE service_id = %s
                AND title_engaged_id = %s 
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(
            patch_labour_cost_sql,
            [updated_required_time, int(service_id), int(title_engaged_id)],
        )
