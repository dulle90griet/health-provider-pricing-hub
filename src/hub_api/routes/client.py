"""Provides method-specific routes for /client API routes."""

from typing_extensions import Annotated
from psycopg.sql import SQL, Identifier, Placeholder
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from hub_api.logger import logger
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql
from hub_api.models.requests import ClientLaxList, UpdateClient


# @app.get("/client")
def get_client(
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """GET method for client table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)

    valid_search_columns = ["client_name"]
    search_sql = build_search_sql(
        queries.search_column,
        queries.search_string,
        valid_search_columns,
    )

    valid_sort_columns = ["id", "client_name"]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("client_name").to_sql()

    get_client_sql = SQL("""
        SELECT *
        FROM client
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
        cursor.execute(get_client_sql)
        results = cursor.fetchall()

    return results


# @app.get("/client/names")
def get_client_names() -> list:
    """
    Method to GET all client names in the client table
    Used for populating client-selection dropdown lists
    """
    sort_clause = SortClauses("client_name").to_sql()
    get_client_names_sql = SQL("""
        SELECT
            id AS client_id
            ,client_name
        FROM client
        {sort_clause}
    """).format(sort_clause=sort_clause)

    with DatabaseCursor() as cursor:
        cursor.execute(get_client_names_sql)
        results = cursor.fetchall()

    return results


# @app.post("/client")
def post_client(body: Annotated[ClientLaxList, Body()]) -> None:
    """POST method for client table"""
    columns = ("client_name",)
    rows = body.root

    logger.info("POST into client values:")
    logger.info(rows)

    values = [row.model_dump()[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO client ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


# @app.patch("/client/<client_id>")
def patch_client(client_id: str, body: Annotated[UpdateClient, Body()]) -> None:
    """PATCH method for client table"""
    logger.info("PATCHing client ID: %s", client_id)
    logger.info(body)

    if "client_name" not in body.model_fields_set:
        return None
    updated_client_name = body.model_dump()["client_name"]

    patch_direct_cost_sql = SQL("""
            UPDATE client
            SET client_name = %s
            WHERE id = %s
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(
            patch_direct_cost_sql,
            [updated_client_name, int(client_id)],
        )

    return None
