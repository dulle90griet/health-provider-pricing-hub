"""Pydantic models for requests on /tender routes."""

from datetime import datetime
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model
from hub_api.models import build_lax_list_model


class Tender(BaseModel):
    """
    A defined tender in the system.
    Model underlying POST requests.
    """

    tender_title: Annotated[str, Field(max_length=50)]
    client_id: Annotated[int, Field(ge=1, le=2**31 - 1)]
    projected_sales_value_gbp: Annotated[int, Field(ge=-(2**31), le=2**31 - 1)]
    date_created: datetime


TenderLaxList = build_lax_list_model(Tender)  # LaxList for POST

UpdateTender = create_partial_model(Tender)  # Partial model for PATCH
