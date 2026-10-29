"""Pydantic models for requests on /client routes."""

from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model


class Client(BaseModel):
    """A defined client in the system. Model used for POST requests."""

    client_name: Annotated[str, Field(max_length=50)]


UpdateClient = create_partial_model(Client)  # Partial model for PATCH
