"""
LaxList RootModel factory, allowing Pydantic validation
of model and list[model] alike"""

from typing import TypeVar, ClassVar, Type
from pydantic import BaseModel, RootModel, model_validator


T = TypeVar("T", bound="BaseModel")


def build_lax_list_model(model: Type[T]) -> Type[RootModel[list[T]]]:
    """
    Factory function: creates a RootModel that coerces a single dict
    into a list of dicts for *model*.
    """

    class LaxList(RootModel[list[model]]):
        item_model: ClassVar[type] = model

        @model_validator(mode="before")
        @classmethod
        def coerce_single(cls, values):
            return [values] if isinstance(values, dict) else values

        @model_validator(mode="after")
        def check_not_empty(self):
            if len(self.root) == 0:
                raise ValueError("at least one row object required")
            return self

    LaxList.__name__ = f"{model.__name__}List"
    LaxList.__module__ = model.__module__
    return LaxList
