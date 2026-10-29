"""Pydantic models for requests on /client routes."""

from typing_extensions import Annotated
from pydantic import BaseModel, Field
from pydantic_strict_partial import create_partial_model
from hub_api.models import build_lax_list_model


class Client(BaseModel):
    """A defined client in the system. Model underlying POST requests."""

    client_name: Annotated[str, Field(max_length=50)]


ClientLaxList = build_lax_list_model(Client)  # LaxList for POST

UpdateClient = create_partial_model(Client)  # Partial model for PATCH
