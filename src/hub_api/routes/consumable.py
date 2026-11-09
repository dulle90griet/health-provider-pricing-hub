"""Provides method-specific routes for /consumable API routes."""

from typing_extensions import Annotated
from psycopg.sql import SQL, Identifier, Placeholder
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from hub_api.logger import logger
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql
from hub_api.models.requests import ConsumableLaxList, UpdateConsumable


# @app.get("/consumable")
def get_consumable(
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """GET method for consumable table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)
    sort_clauses = SortClauses(sort)

    valid_search_columns = ["consumable_name"]
    search_sql = build_search_sql(
        queries.search_column, queries.search_string, valid_search_columns
    )

    valid_sort_columns = [
        "id",
        "consumable_name",
        "default_unit_cost_gbp",
    ]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("consumable_name").to_sql()

    get_sql = SQL("""
        SELECT *
        FROM consumable
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

    return results


# @app.get("/consumable/names")
def get_consumable_names() -> list:
    """
    Method to GET all consumable names in the consumable table
    Used for populating consumable-selection dropdown lists
    """
    sort_clause = SortClauses("consumable_name").to_sql()
    get_consumable_names_sql = SQL("""
        SELECT
            id AS consumable_id
            ,consumable_name
        FROM consumable
        {sort_clause}
    """).format(sort_clause=sort_clause)

    with DatabaseCursor() as cursor:
        cursor.execute(get_consumable_names_sql)
        results = cursor.fetchall()

    return results


# @app.post("/consumable")
def post_consumable(body: Annotated[ConsumableLaxList, Body()]) -> None:
    """POST method for consumable table"""
    columns = ("consumable_name", "default_unit_cost_gbp")

    rows = body.root

    logger.info("POST into consumable values:")
    logger.info(rows)

    values = [row.model_dump()[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO consumable ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


# @app.patch("/consumable/<consumable_id>")
def patch_consumable(
    consumable_id: int, body: Annotated[UpdateConsumable, Body()]
) -> None:
    """PATCH method for consumable table"""

    logger.info("PATCHing consumable ID: %s", consumable_id)
    logger.info(body)

    updated_columns = body.model_dump(exclude_unset=True)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("UPDATE consumable SET {} WHERE ID = %s").format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [int(consumable_id)])
