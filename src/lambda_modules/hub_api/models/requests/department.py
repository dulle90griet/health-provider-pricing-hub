"""Pydantic models for requests on /department routes."""

from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model
from hub_api.models import build_lax_list_model


class Department(BaseModel):
    """
    A defined department in the system.
    Model underlying POST requests.
    """

    name: Annotated[str, Field(max_length=50)]


DepartmentLaxList = build_lax_list_model(Department)  # LaxList for POST

UpdateDepartment = create_partial_model(Department)  # Partial model for PATCH
