"""Provides method-specific routes for the /tender/line-items/rich API route."""

from typing_extensions import Annotated
from psycopg.sql import SQL
from aws_lambda_powertools.event_handler.openapi.params import Query
from hub_api.db import DatabaseCursor
from hub_api.models.params import URIQueries, SortClauses, build_search_sql


overhead_recovery_on_labour_cost_gbp = """
    base.labour_cost_gbp * base.overhead_recovery_on_labour_percentage / 100
"""
fully_absorbed_cost_gbp = f"""
    base.labour_cost_gbp + ({overhead_recovery_on_labour_cost_gbp}) + base.direct_cost_gbp
"""
profit_margin_gbp = f"""
    ({fully_absorbed_cost_gbp})
    / (1 - (base.required_profit_margin_percentage / 100))
    * (base.required_profit_margin_percentage / 100)
"""
recommended_unit_price_gbp = f"""
    ({fully_absorbed_cost_gbp}) + ({profit_margin_gbp})
"""
unit_price_to_use = """
    COALESCE(base.unit_price_override_gbp, base.our_current_unit_price_gbp)
"""
annual_sales_gbp = f"({unit_price_to_use}) * base.total_number_pa"
annual_labour_gbp = "base.labour_cost_gbp * base.total_number_pa"
annual_direct_gbp = "base.direct_cost_gbp * base.total_number_pa"
annual_overhead_gbp = f"({overhead_recovery_on_labour_cost_gbp}) * base.total_number_pa"
annual_total_gbp = f"""
    ({annual_labour_gbp}) + ({annual_direct_gbp}) + ({annual_overhead_gbp})
"""
annual_profit_gbp = f"""
    ({annual_sales_gbp}) - ({annual_total_gbp})
"""


# @app.get("/tender/line-items/rich/<tender_id>")
def get_rich_tender_line_items(
    tender_id: int,
    queries: Annotated[URIQueries, Query()],
    sort: Annotated[list[str], Query()] = "",
) -> list:
    """Enriched GET method for tenders_services table"""
    max_per_page = 100
    page = max(int(queries.page), 1)
    per_page = min(max(int(queries.per_page), 1), max_per_page)
    offset = per_page * (page - 1)

    valid_search_columns = [
        "base.service_category",
        "base.service",
    ]
    search_sql = build_search_sql(
        queries.search_column,
        queries.search_string,
        valid_search_columns,
    )

    valid_sort_columns = [
        "service_category",
        "service_id",
        "service",
        "total_number_pa",
        "unit_labour_cost_gbp",
        "overhead_recovery_on_labour_percentage",
        "overhead_recovery_on_labour_cost_gbp",
        "unit_direct_cost_gbp",
        "fully_absorbed_cost_gbp",
        "required_profit_margin_percentage",
        "profit_margin_gbp",
        "recommended_unit_price_gbp",
        "our_current_unit_price_gbp",
        "unit_price_override_gbp",
        "annual_sales_gbp",
        "annual_labour_gbp",
        "annual_direct_gbp",
        "annual_overhead_gbp",
        "annual_total_gbp",
        "annual_profit_gbp",
    ]
    sort_clauses = SortClauses(sort, whitelist=valid_sort_columns)
    sort_clause_sql = sort_clauses.to_sql()
    if not sort_clause_sql:
        sort_clause_sql = SortClauses("base.service_category", "base.service").to_sql()

    get_rich_line_items_sql = SQL(f"""
        WITH
            tender_line_items_filtered AS (
                SELECT *
                FROM tenders_services
                WHERE tender_id = {{tender_id}}
            )
            ,labour_costs_summed AS (
                SELECT
                    service_id
                    ,SUM(jt.hourly_rate_gbp * lc.required_time_mins / 60)
                        AS total_cost_gbp
                FROM labour_cost lc
                LEFT OUTER JOIN job_title jt
                    ON lc.title_engaged_id = jt.id
                GROUP BY service_id
            )
            ,direct_costs_summed AS (
                SELECT
                    service_id
                    ,SUM(cost_gbp) AS total_cost_gbp
                FROM direct_cost
                GROUP BY service_id
            )
            ,base AS (
                SELECT
                    ft.tender_id
                    ,t.tender_title
                    ,s.category AS service_category
                    ,ft.service_id
                    ,s.service_name AS service
                    ,ft.total_number_pa
                    ,COALESCE(lc.total_cost_gbp, 0) AS labour_cost_gbp
                    ,200 AS overhead_recovery_on_labour_percentage
                    ,COALESCE(dc.total_cost_gbp, 0) AS direct_cost_gbp
                    ,s.required_profit_margin_percentage
                    ,s.our_current_unit_price_gbp
                    ,ft.unit_price_override_gbp
                FROM tender_line_items_filtered ft
                LEFT OUTER JOIN tender t
                    ON ft.tender_id = t.id
                LEFT OUTER JOIN service s
                    ON ft.service_id = s.id
                LEFT OUTER JOIN labour_costs_summed lc
                    ON ft.service_id = lc.service_id
                LEFT OUTER JOIN direct_costs_summed dc
                    ON ft.service_id = dc.service_id
            )
        SELECT
            base.tender_id
            ,base.tender_title
            ,base.service_category
            ,base.service_id
            ,base.service
            ,base.total_number_pa
            ,ROUND(base.labour_cost_gbp, 4) AS unit_labour_cost_gbp
            ,base.overhead_recovery_on_labour_percentage
            ,ROUND({overhead_recovery_on_labour_cost_gbp}, 4)
                AS overhead_recovery_on_labour_cost_gbp
            ,ROUND(base.direct_cost_gbp, 4) AS unit_direct_cost_gbp
            ,ROUND({fully_absorbed_cost_gbp}, 4) AS fully_absorbed_cost_gbp
            ,base.required_profit_margin_percentage
            ,ROUND({profit_margin_gbp}, 4) AS profit_margin_gbp
            ,ROUND({recommended_unit_price_gbp}, 4) AS recommended_unit_price_gbp
            ,base.our_current_unit_price_gbp
            ,base.unit_price_override_gbp
            ,ROUND({annual_sales_gbp}, 4) AS annual_sales_gbp
            ,ROUND({annual_labour_gbp}, 4) AS annual_labour_gbp
            ,ROUND({annual_direct_gbp}, 4) as annual_direct_gbp
            ,ROUND({annual_overhead_gbp}, 4) as annual_overhead_gbp
            ,ROUND({annual_total_gbp}, 4) AS annual_total_gbp
            ,ROUND({annual_profit_gbp}, 4) AS annual_profit_gbp
        FROM base
        {{search_clause}}
        {{sort_clause}}
        LIMIT {{per_page}}
        OFFSET {{offset}}
    """).format(
        tender_id=tender_id,
        search_clause=search_sql,
        sort_clause=sort_clause_sql,
        per_page=per_page,
        offset=offset,
    )

    with DatabaseCursor() as cursor:
        cursor.execute(get_rich_line_items_sql)
        results = cursor.fetchall()

    return results


# @app.get("/tender/line-items/<tender_id>/totals")
def get_rich_tender_line_items_totals(tender_id: int) -> list:
    get_totals_sql = SQL(f"""
        WITH
            tender_line_items_filtered AS (
                SELECT *
                FROM tenders_services
                WHERE tender_id = {{tender_id}}
            )
            ,labour_costs_summed AS (
                SELECT
                    lc.service_id
                    ,SUM(jt.hourly_rate_gbp * lc.required_time_mins / 60)
                        AS total_cost_gbp
                FROM labour_cost lc
                LEFT OUTER JOIN job_title jt
                    ON lc.title_engaged_id = jt.id
                WHERE lc.service_id
                    IN (SELECT service_id FROM tender_line_items_filtered)
                GROUP BY service_id
            )
            ,direct_costs_summed AS (
                SELECT
                    service_id
                    ,SUM(cost_gbp) AS total_cost_gbp
                FROM direct_cost
                WHERE service_id
                    IN (SELECT service_id FROM tender_line_items_filtered)
                GROUP BY service_id
            )
            ,base AS (
                SELECT
                    ft.tender_id
                    ,t.tender_title
                    ,ft.total_number_pa
                    ,COALESCE(lc.total_cost_gbp, 0) AS labour_cost_gbp
                    ,200 AS overhead_recovery_on_labour_percentage
                    ,COALESCE(dc.total_cost_gbp, 0) AS direct_cost_gbp
                    ,s.our_current_unit_price_gbp
                    ,ft.unit_price_override_gbp
                FROM tender_line_items_filtered ft
                LEFT OUTER JOIN tender t
                    ON ft.tender_id = t.id
                LEFT OUTER JOIN service s
                    ON ft.service_id = s.id
                LEFT OUTER JOIN labour_costs_summed lc
                    ON ft.service_id = lc.service_id
                LEFT OUTER JOIN direct_costs_summed dc
                    ON ft.service_id = dc.service_id
            )
            ,sums AS (
                SELECT
                    COALESCE(SUM({annual_sales_gbp}), 0) AS total_annual_sales_gbp
                    ,COALESCE(SUM({annual_labour_gbp}), 0) AS total_annual_labour_gbp
                    ,COALESCE(SUM({annual_direct_gbp}), 0) AS total_annual_direct_gbp
                    ,COALESCE(SUM({annual_overhead_gbp}), 0) AS total_annual_overhead_gbp
                    ,COALESCE(SUM({annual_total_gbp}), 0) AS total_annual_total_gbp
                    ,COALESCE(SUM({annual_profit_gbp}), 0) AS total_annual_profit_gbp
                FROM base
            )
        SELECT
            t.id AS tender_id
            ,t.tender_title
            ,ROUND(s.total_annual_sales_gbp, 4) AS total_annual_sales_gbp
            ,ROUND(s.total_annual_labour_gbp, 4) AS total_annual_labour_gbp
            ,ROUND(s.total_annual_direct_gbp, 4) AS total_annual_direct_gbp
            ,ROUND(s.total_annual_overhead_gbp, 4) AS total_annual_overhead_gbp
            ,ROUND(s.total_annual_total_gbp, 4) AS total_annual_total_gbp
            ,ROUND(s.total_annual_profit_gbp, 4) AS total_annual_profit_gbp
        FROM sums s
        LEFT OUTER JOIN tender t
            ON t.id = {{tender_id}}
    """).format(
        tender_id=tender_id,
    )

    with DatabaseCursor() as cursor:
        cursor.execute(get_totals_sql)
        results = cursor.fetchall()

    return results
