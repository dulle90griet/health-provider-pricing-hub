"""Provides method-specific handlers for the /department API route."""

from psycopg.sql import SQL

# from hub_api.resolver import app
from hub_api.db import DatabaseCursor
from hub_api.models.params import SortClauses


# @app.get("/department")
def get_department() -> list:
    """GET method for department table"""
    sort_clause_sql = SortClauses("name").to_sql()

    get_department_sql = SQL("""
        SELECT *
        FROM department
        {sort_clause}
    """).format(sort_clause=sort_clause_sql)

    with DatabaseCursor() as cursor:
        cursor.execute(get_department_sql)
        results = cursor.fetchall()

    return results
