"""Pydantic models for requests on /labour-cost routes."""

from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model
from hub_api.models import build_lax_list_model


class LabourCost(BaseModel):
    """
    A defined labour cost in the system.
    Model underlying POST requests.
    """

    service_id: Annotated[int, Field(ge=1, le=2**31 - 1)]
    title_engaged_id: Annotated[int, Field(ge=1, le=2**31 - 1)]
    required_time_mins: Annotated[int, Field(ge=0, le=2**31 - 1)]


LabourCostLaxList = build_lax_list_model(LabourCost)  # LaxList for POST

UpdateLabourCost = create_partial_model(LabourCost)  # Partial model for PATCH
