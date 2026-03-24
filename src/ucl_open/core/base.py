from typing import Literal


class DiscriminatorTypeMixin:
    """Mixin to set `discriminator_type` to the subclass name for types participating in a discriminated union."""

    def __init_subclass__(cls, **kwargs):
        """Injects `discriminator_type` as a Literal of the subclass name."""
        super().__init_subclass__(**kwargs)
        name = cls.__name__
        cls.__annotations__["discriminator_type"] = Literal[name]
        cls.discriminator_type = name
