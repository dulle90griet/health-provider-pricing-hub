"""Pydantic models for requests on /department routes."""

from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model


class Department(BaseModel):
    """A defined department in the system. Model used for POST requests."""

    name: Annotated[str, Field(max_length=50)]


UpdateDepartment = create_partial_model(Department)  # Partial model for PATCH
