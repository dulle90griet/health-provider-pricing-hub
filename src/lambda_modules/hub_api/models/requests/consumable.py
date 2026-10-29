"""Pydantic models for requests on /consumable routes."""

from decimal import Decimal
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model
from hub_api.models import OptionalDecimal


class Consumable(BaseModel):
    """A defined consumable in the system. Model used for POST requests."""

    consumable_name: Annotated[str, Field(max_length=100)]
    default_unit_cost_gbp: Annotated[Decimal | None, OptionalDecimal(8, 4)] = None


UpdateConsumable = create_partial_model(Consumable)  # Partial model for PATCH
