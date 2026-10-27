"""OptionalDecimal Type factory for use in Pydantic models"""

from decimal import Decimal, InvalidOperation as InvalidDecimalOperation
from typing import TypeAlias
from typing_extensions import Annotated
from pydantic import Field, BeforeValidator


def build_optional_decimal_type(max_digits: int, decimal_places: int) -> TypeAlias:
    """
    Create an Optional Decimal type with empty string handling and constraints.

    Args:
        max_digits: Maximum total number of digits
        decimal_places: Maximum number of decimal places

    Returns:
        A type alias that can be used in Pydantic models
    """
    return Annotated[
        None
        | Annotated[
            Decimal, Field(max_digits=max_digits, decimal_places=decimal_places)
        ],
        BeforeValidator(_empty_to_none),
    ]


def _empty_to_none(value: str | Decimal | None) -> Decimal | None:
    """
    Convert empty strings to None for optional Decimal fields.

    This validator runs before Pydantic's built-in validation,
    so empty strings are treated as None instead of raising an error.

    Also accepts a string of "-", as a workaround for systems incapable
    of sending JSON null values.
    """
    if value in ("", "-", None):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError("Boolean values are not allowed for Decimal fields")
    try:
        return Decimal(value)
    except (InvalidDecimalOperation, TypeError) as e:
        raise ValueError(f"Invalid decimal value: {value}") from e
