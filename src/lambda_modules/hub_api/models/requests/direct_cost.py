"""Pydantic models for requests on /direct-cost routes."""

from decimal import Decimal
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model


class DirectCost(BaseModel):
    """
    A defined direct cost in the system.
    Model used for POST requests.
    """

    service_id: Annotated[int, Field(ge=1, le=2**31 - 1)]
    consumable_id: Annotated[int, Field(ge=1, le=2**31 - 1)]
    cost_gbp: Annotated[Decimal, Field(max_digits=7, decimal_places=4)]


UpdateDirectCost = create_partial_model(DirectCost)  # Partial model for PATCH
