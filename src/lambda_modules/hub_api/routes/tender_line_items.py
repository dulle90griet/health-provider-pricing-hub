"""Provides method-specific routes for /labour-cost API routes."""

from typing_extensions import Annotated
from psycopg.sql import SQL, Identifier, Placeholder
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from hub_api.logger import logger
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql
from hub_api.models.requests import TenderLineItemLaxList, UpdateTenderLineItem


# @app.get("/tender/line-items/<tender_id>")
def get_tender_line_items(
    tender_id: str,
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """GET method for tenders_services table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)

    valid_search_columns = [
        "service",
    ]
    search_sql = build_search_sql(
        queries.search_column,
        queries.search_string,
        valid_search_columns,
    )

    valid_sort_columns = [
        "service_id",
        "service",
        "total_number_pa",
        "unit_price_override_gbp",
    ]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("s.service_name").to_sql()

    get_line_items_sql = SQL("""
        WITH filtered_tender_line_items AS (
            SELECT *
            FROM tenders_services
            WHERE tender_id = {tender_id}
        )
        SELECT
            ft.tender_id
            ,t.tender_title
            ,ft.service_id
            ,s.service_name AS service
            ,ft.total_number_pa
            ,ft.unit_price_override_gbp
        FROM filtered_tender_line_items ft
        LEFT OUTER JOIN tender t
            ON ft.tender_id = t.id
        LEFT OUTER JOIN service s
            ON ft.service_id = s.id
        {search_clause}
        {sort_clause}
        LIMIT {per_page}
        OFFSET {offset}
    """).format(
        tender_id=tender_id,
        search_clause=search_sql,
        sort_clause=sort_clause_sql,
        per_page=per_page,
        offset=offset,
    )

    with DatabaseCursor() as cursor:
        cursor.execute(get_line_items_sql)
        results = cursor.fetchall()

    return results


# @app.post("/tender/line-items")
def post_tender_line_items(body: Annotated[TenderLineItemLaxList, Body()]) -> None:
    """POST method for tenders_services table"""
    columns = (
        "tender_id",
        "service_id",
        "total_number_pa",
        "unit_price_override_gbp",
    )
    rows = body.root

    logger.info("POST into tenders_services values:")
    logger.info(rows)

    values = [row.model_dump()[column] for column in columns for row in rows]
    placeholders = SQL(", ").join(
        SQL("({})").format(SQL(", ").join(Placeholder() * len(columns))) for _ in rows
    )
    post_sql = SQL("INSERT INTO tenders_services ({}) VALUES {}").format(
        SQL(", ").join(map(Identifier, columns)),
        placeholders,
    )

    with DatabaseCursor() as cursor:
        logger.info(post_sql.as_string(cursor))
        cursor.execute(post_sql, values)


# @app.patch("/tender/line-items/<tender_id>/<service_id>")
def patch_tender_line_item(
    tender_id: str, service_id: str, body: Annotated[UpdateTenderLineItem, Body()]
) -> None:
    """PATCH method for tenders_services table"""
    logger.info(
        "PATCHing tenders_services ID %s, service ID %s",
        tender_id,
        service_id,
    )
    logger.info(body)

    updated_columns = body.model_dump(exclude_unset=True)

    set_parts = []
    values = []
    for col, val in updated_columns.items():
        set_parts.append(SQL("{} = %s").format(Identifier(col)))
        values.append(val)

    patch_sql = SQL("""
        UPDATE tenders_services
        SET {}
        WHERE tender_id = %s
          AND service_id = %s
    """).format(SQL(", ").join(set_parts))

    with DatabaseCursor() as cursor:
        cursor.execute(patch_sql, values + [tender_id, service_id])
