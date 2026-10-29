"""Pydantic models for requests on /job-title routes."""

from decimal import Decimal
from typing import TypeAlias
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model
from hub_api.models import OptionalDecimal, build_lax_list_model


OptionalDecimal3x1: TypeAlias = Annotated[Decimal | None, OptionalDecimal(3, 1)]


class JobTitle(BaseModel):
    """
    A defined job title in the system.
    Model underlying POST requests.
    """

    department_id: Annotated[int, Field(ge=1, le=2**31 - 1)]
    title: Annotated[str, Field(max_length=50)]
    default_ft_weekly_hours: Annotated[Decimal, Field(max_digits=3, decimal_places=1)]
    default_lunch_break_mins: Annotated[int, Field(ge=0, le=240)]
    hourly_rate_gbp: Annotated[Decimal, Field(max_digits=7, decimal_places=4)]
    default_annual_holiday_days: OptionalDecimal3x1 = None
    default_annual_training_days: OptionalDecimal3x1 = None
    default_annual_sick_days: OptionalDecimal3x1 = None


JobTitleLaxList = build_lax_list_model(JobTitle)  # LaxList for POST

UpdateJobTitle = create_partial_model(JobTitle)  # Partial model for PATCH
