"""Pydantic models for requests on /overhead-cost routes."""

from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model


class OverheadCost(BaseModel):
    """
    A defined overhead cost in the system.
    Model used for POST requests.
    """

    cost_type: Annotated[str, Field(max_length=30)]
    cost_description: Annotated[str, Field(max_length=30)]
    budgeted_spend_gbp: Annotated[int, Field(ge=-(2**31), le=2**31 - 1)]


UpdateOverheadCost = create_partial_model(OverheadCost)  # Partial model for PATCH
