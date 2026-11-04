from psycopg.sql import Composable, SQL, Identifier
from hub_api.exceptions import InvalidParameterError


def build_search_sql(
    search_column: str, search_string: str, whitelist: list[str] = None
) -> Composable:
    """
    Given a search column and a search string, return
    an injection-resistant psycopg Composable SQL clause
    for case-insensitive filtering ('WHERE ... ILIKE ...').

    Args:
        search_column (str):
            The name of the column to search.
        search_string (str):
            The string to search for in that column.
        whitelist (list[str], optional):
            A list of accepted column names. If supplied, any column
            not on this list will be rejected.
    """

    if not search_column or not search_string:
        return SQL("")

    if whitelist and search_column not in whitelist:
        raise InvalidParameterError("Provided search column is not whitelisted.")

    column_parts = search_column.split(".")
    if len(column_parts) <= 2:
        search_column_identifier = Identifier(*column_parts)
    else:
        raise InvalidParameterError(
            f"Qualified reference of more than two parts: {search_column}"
        )

    return SQL("WHERE {} ILIKE {}").format(
        search_column_identifier, f"%{search_string}%"
    )
