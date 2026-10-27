from typing import Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field


class URIQueries(BaseModel):
    """
    Pydantic model validating URI/URL query parameters
    as received by API Gateway
    """

    page: Optional[int] = 1
    per_page: Optional[int] = 10
    search_column: Annotated[Optional[str], Field(max_length=40)] = None
    search_string: Annotated[Optional[str], Field(max_length=30)] = None
