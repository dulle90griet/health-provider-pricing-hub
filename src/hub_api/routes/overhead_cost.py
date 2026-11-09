"""Provides method-specific routes for /overhead-cost API routes."""

from typing_extensions import Annotated
from psycopg.sql import SQL, Identifier, Placeholder
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from hub_api.logger import logger
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql
from hub_api.models.requests import OverheadCostLaxList, UpdateOverheadCost


# @app.get("/overhead-cost")
def get_overhead_cost(
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """GET method for overhead_cost table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)

    valid_search_columns = [
        "cost_type",
        "cost_description",
    ]
    search_sql = build_search_sql(
        queries.search_column,
        queries.search_string,
        valid_search_columns,
    )

    valid_sort_columns = [
        "id",
        "cost_type",
        "cost_description",
        "budgeted_spend_gbp",
    ]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("cost_type", "cost_description").to_sql()

    get_overhead_cost_sql = SQL("""
        SELECT *
        FROM overhead_cost
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
        cursor.execute(get_overhead_cost_sql)
        results = cursor.fetchall()

    logger.info(results)
    return results


# @app.post("/overhead-cost")
def post_overhead_cost(body: Annotated[OverheadCostLaxList, Body()]) -> None:
    """POST method for overhead_cost table"""
    columns = ("cost_type", "cost_description", "budgeted_spend_gbp")
    rows = body.root

    logger.info("POST into overhead_cost values:")
    logger.info(rows)

    values = [
        row.model_dump()[column] if row.model_dump()[column] != "null" else None
        for column in columns
        for row in rows
    ]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_overhead_cost_sql = SQL("INSERT INTO overhead_cost ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        # logger.info(post_overhead_cost_sql.as_string(cursor))
        cursor.execute(post_overhead_cost_sql, values)


# @app.patch("/overhead-cost/<overhead_cost_id>")
def patch_overhead_cost(
    overhead_cost_id: int, body: Annotated[UpdateOverheadCost, Body()]
) -> None:
    """PATCH method for overhead_cost table"""
    logger.info("PATCHing overhead_cost ID: %s", overhead_cost_id)
    logger.info(body)

    updated_columns = body.model_dump(exclude_unset=True)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_overhead_cost_sql = SQL("UPDATE overhead_cost SET {} WHERE ID = %s").format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_overhead_cost_sql, values + [int(overhead_cost_id)])
