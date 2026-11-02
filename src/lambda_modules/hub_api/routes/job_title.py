"""Provides method-specific handlers for /job-title API routes."""

from typing_extensions import Annotated
from psycopg.sql import SQL
from aws_lambda_powertools.event_handler.openapi.params import Query
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql


# @app.get("/job-title")
def get_job_title(
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """GET method for job_title table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)

    valid_search_columns = [
        "d.name",
        "title",
    ]
    search_sql = build_search_sql(
        queries.search_column,
        queries.search_string,
        valid_search_columns,
    )

    valid_sort_columns = [
        "jt.id",
        "jt.department.id",
        "department",
        "title",
        "default_ft_weekly_hours",
        "default_lunch_break_mins",
        "hourly_rate_gbp",
        "default_annual_holiday_days",
        "default_annual_training_days",
        "default_annual_sick_days",
    ]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("department", "jt.title").to_sql()

    get_job_title_sql = SQL("""
        SELECT
            jt.id
            ,jt.department_id
            ,d.name AS department
            ,jt.title
            ,jt.default_ft_weekly_hours
            ,jt.default_lunch_break_mins
            ,jt.hourly_rate_gbp
            ,jt.default_annual_holiday_days
            ,jt.default_annual_training_days
            ,jt.default_annual_sick_days
        FROM job_title jt
        LEFT OUTER JOIN department d
            ON jt.department_id = d.id
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
        cursor.execute(get_job_title_sql)
        results = cursor.fetchall()

    return results
