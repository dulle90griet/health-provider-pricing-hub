"""OptionalDecimal custom annotation for use in Pydantic models"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation as InvalidDecimalOperation
from typing import Any, TypeAlias
from typing_extensions import Annotated
from pydantic import Field, GetCoreSchemaHandler, BeforeValidator
from pydantic_core import core_schema


@dataclass(frozen=True)
class OptionalDecimal:
    """
    Optional Decimal type annotation with empty string handling
    (via _empty_to_none() BeforeValidator) and constraints applied
    only if a decimal value is provided.
    """

    max_digits: int
    decimal_places: int

    def __get_pydantic_core_schema__(
        self, _: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        inner = handler(
            Annotated[
                Decimal,
                Field(
                    max_digits=self.max_digits,
                    decimal_places=self.decimal_places,
                ),
            ]
        )
        return core_schema.no_info_before_validator_function(
            _empty_to_none, core_schema.nullable_schema(inner)
        )


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
