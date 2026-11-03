"""Provides method-specific routes for /labour-cost API routes."""

from typing_extensions import Annotated
from psycopg.sql import SQL, Identifier, Placeholder
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from hub_api.logger import logger
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql
from hub_api.models.requests import TenderLaxList, UpdateTender


# @app.get("/tender")
def get_tender(
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """GET method for tender table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)

    valid_search_columns = [
        "tender_title",
        "c.client_name",
    ]
    search_sql = build_search_sql(
        queries.search_column,
        queries.search_string,
        valid_search_columns,
    )

    valid_sort_columns = [
        "id",
        "tender_title",
        "client_id",
        "client",
        "projected_sales_value_gbp",
        "date_created",
    ]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("-t.date_created").to_sql()

    get_tender_sql = SQL("""
        SELECT
            t.id
            ,t.tender_title
            ,t.client_id
            ,c.client_name AS client
            ,t.projected_sales_value_gbp
            ,t.date_created
        FROM tender t
        LEFT OUTER JOIN client c
            ON t.client_id = c.id
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

    logger.info(f"get_sql: {get_tender_sql.as_string()}")

    with DatabaseCursor() as cursor:
        cursor.execute(get_tender_sql)
        results = cursor.fetchall()

    return results


# @app.get("/tender/single/<tender_id>")
def get_tender_single(tender_id: str):
    """
    Method to GET the tender record for the supplied id
    """
    get_tender_sql = SQL("""
        SELECT
            t.id
            ,t.tender_title
            ,t.client_id
            ,c.client_name AS client
            ,t.projected_sales_value_gbp
            ,t.date_created
        FROM tender t
        LEFT OUTER JOIN client c
            ON t.client_id = c.id
        WHERE t.id = %s
    """)

    with DatabaseCursor() as cursor:
        cursor.execute(get_tender_sql, [int(tender_id)])
        results = cursor.fetchall()

    return results


# @app.get("/tender/titles")
def get_tender_titles() -> list:
    """
    Method to GET all tender titles in the tender table
    Used for populating tender-selection dropdown lists
    """
    sort_clause_sql = SortClauses("tender_title").to_sql()
    get_tender_titles_sql = SQL("""
        SELECT
            id AS tender_id
            ,tender_title
        FROM tender
        {sort_clause}
    """).format(sort_clause=sort_clause_sql)

    with DatabaseCursor() as cursor:
        cursor.execute(get_tender_titles_sql)
        results = cursor.fetchall()

    return results


# @app.post("/tender")
def post_tender(body: Annotated[TenderLaxList, Body()]) -> None:
    """POST method for tender table"""
    columns = ("tender_title", "client_id", "projected_sales_value_gbp", "date_created")
    rows = body.root

    logger.info("POST into tender values:")
    logger.info(rows)

    values = [row.model_dump()[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO tender ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


# @app.patch("/tender/<tender_id>")
def patch_tender(tender_id: str, body: Annotated[UpdateTender, Body()]) -> None:
    """PATCH method for tender table"""
    logger.info("PATCHing tender ID: %s", tender_id)
    logger.info(body)

    updated_columns = body.model_dump(exclude_unset=True)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("UPDATE tender SET {} WHERE ID = %s").format(
        SQL(", ").join(set_parts)
    )

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [int(tender_id)])
