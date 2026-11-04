"""
Provides the Pydantic models and helper used to validate
sort clauses provided by URIQueries
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator
from psycopg.sql import Composable, SQL, Identifier

from hub_api.exceptions import InvalidParameterError
from .whitelist import filter_by_whitelist


class SortClause(BaseModel):
    """
    Pydantic model performing rudimentary validation
    of a single received sort clause
    """

    column: str
    direction: Literal["ASC", "DESC"] = "ASC"


class SortClauses(BaseModel):
    """
    Pydantic model validating a list of SortClauses
    and offering whitelist-checked psycopg3 sort SQL generation
    """

    clauses: list[SortClause] = Field(default_factory=list)
    whitelist: list[str] = None

    def __init__(self, *sort_strings, **kwargs):
        """
        Initialize SortClauses from either SortClause objects
        or sort strings.

        Supports multiple invocation styles:
        - From existing SortClause objects:
            SortClauses(clauses=[...])
        - From individual sort strings:
            SortClauses("-service_id", "title_engaged")
        - From a list of sort strings:
            SortClauses(["-service_id", "title_engaged"])

        The keyword argument `whitelist` is compatible with all styles.

        Raises:
            ValueError: If duplicate columns are detected in the
                sort clauses.
        """
        if len(sort_strings) == 1 and isinstance(sort_strings[0], list):
            kwargs["clauses"] = _parse_sort_strings(list(sort_strings[0]))
        elif sort_strings:
            kwargs["clauses"] = _parse_sort_strings(list(sort_strings))
        super().__init__(**kwargs)

    @field_validator("clauses")
    @classmethod
    def validate_no_duplicates(cls, value: list[SortClause]) -> list[SortClause]:
        """Confirm the provided list features each column at most once."""
        columns = [c.column for c in value]
        if len(columns) != len(set(columns)):
            raise ValueError("Duplicate sort column provided")
        return value

    def to_sql(self) -> Composable | Literal[""]:
        """
        Build a single- or multi-level ORDER BY clause
        using the contents of the SortClause object's `clauses` list.

        Returns "" if `clauses` is empty or contains columns
        not present in the provided whitelist.
        """
        if not self.clauses:
            return ""

        # Proceed only if all provided sort columns are whitelisted
        if self.whitelist:
            if not filter_by_whitelist(
                [c.column for c in self.clauses], self.whitelist, mode="strict"
            ):
                return ""

        sort_parts = []
        for c in self.clauses:
            column_parts = c.column.split(".")
            if len(column_parts) <= 2:
                sort_column = Identifier(*column_parts)
            else:
                raise InvalidParameterError(
                    f"Qualified reference of more than two parts: {c.column}"
                )

            # # DEPRECATED -- CHECK PERFORMED BY PYDANTIC (SEE SORTCLAUSE MODEL)
            # if c.direction.upper() not in ("ASC", "DESC"):
            #     raise InvalidParameterError(f"Invalid order: {c.direction}")

            sort_part = sort_column + SQL(f" {c.direction.upper()}")
            sort_parts.append(sort_part)

        sort_sql = SQL("ORDER BY ") + SQL(", ").join(sort_parts)
        return sort_sql


def _parse_sort_strings(sort_strings: list[str]) -> list[SortClause]:
    """
    Parse a list of sort strings in the format ["col1", "-col2", "col3"]
    (where "-" is descending) into a list of SortClause objects.
    """
    if not sort_strings:
        return []

    clauses = []
    for sort_string in sort_strings:
        if not sort_string:
            continue
        if sort_string[0] == "-" and len(sort_string) >= 2:
            clauses.append(SortClause(column=sort_string[1:], direction="DESC"))
        else:
            clauses.append(SortClause(column=sort_string, direction="ASC"))
    return clauses
