from pydantic import Field
from ucl_open.core.base import BaseSchema


class SyncQuad(BaseSchema):
    """Configuration for the synchronisation quad visual stimulus."""

    extent_x: float = Field(default=0.1, description="Horizontal extent of the quad stimulus.")
    extent_y: float = Field(default=0.1, description="Vertical extent of the quad stimulus.")
    location_x: float = Field(default=-1.0, description="Horizontal position of the quad stimulus.")
    location_y: float = Field(default=-1.0, description="Vertical position of the quad stimulus.")


class RandomFlip(BaseSchema):
    """Configuration for the random ON/OFF flip timing of a visual stimulus."""

    quad_time_lower_bound: float = Field(
        default=0.2, description="Lower bound (s) of the uniform distribution for quad flip timing."
    )
    quad_time_upper_bound: float = Field(
        default=0.5, description="Upper bound (s) of the uniform distribution for quad flip timing."
    )
