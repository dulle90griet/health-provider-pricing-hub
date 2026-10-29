"""Pydantic models for requests on /tender/line-item routes."""

from decimal import Decimal
from typing import TypeAlias
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model
from hub_api.models import OptionalDecimal


OptionalDecimal10x4: TypeAlias = Annotated[Decimal | None, OptionalDecimal(10, 4)]


class TenderLineItem(BaseModel):
    """
    A defined tender line item in the system.
    Model used for POST requests.
    """

    tender_id: Annotated[int, Field(ge=1, le=2**31 - 1)]
    service_id: Annotated[int, Field(ge=1, le=2**31 - 1)]
    total_number_pa: Annotated[int, Field(ge=0, le=2**31 - 1)]
    unit_price_override_gbp: OptionalDecimal10x4 = None


UpdateTenderLineItem = create_partial_model(TenderLineItem)  # Partial model for PATCH
