"""Pydantic models for requests on /service routes."""

from decimal import Decimal
from typing import Optional, TypeAlias
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model
from hub_api.models import OptionalDecimal


OptionalDecimal10x4: TypeAlias = Annotated[Decimal | None, OptionalDecimal(10, 4)]


class Service(BaseModel):
    """A defined service in the system. Model used for POST requests."""

    pillar: Annotated[str, Field(max_length=50)]
    category: Annotated[str, Field(max_length=50)]
    service_name: Annotated[str, Field(max_length=75)]
    xero_code: Annotated[int, Field(ge=0, le=9999)]
    overhead_recovery_on_labour_percentage: Annotated[
        int, Field(ge=-(2**31), le=2**31 - 1)
    ]
    required_profit_margin_percentage: Annotated[
        Decimal, Field(max_digits=5, decimal_places=2)
    ]
    acceptable_market_price_gbp: Annotated[
        Decimal, Field(max_digits=10, decimal_places=4)
    ]
    our_current_unit_price_gbp: Annotated[
        Decimal, Field(max_digits=10, decimal_places=4)
    ]
    new_unit_price_gbp: OptionalDecimal10x4 = None
    new_day_rate_gbp: OptionalDecimal10x4 = None
    comments: Optional[Annotated[str, Field(max_length=100)]] = None


UpdateService = create_partial_model(Service)  # Partial model for PATCH
