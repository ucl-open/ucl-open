from pydantic import Field
from swc.aeon.schema import BaseSchema


class SyncQuad(BaseSchema):
    """Configuration for the synchronisation quad visual stimulus."""

    extent_x: float = Field(default=0.1, ge=0, le=1, description="Horizontal extent of the quad stimulus as a fraction of the total display width.")
    extent_y: float = Field(default=0.1, ge=0, le=1, description="Vertical extent of the quad stimulus as a fraction of the total display height.")
    location_x: float = Field(default=-1.0, ge=0, le=1, description="Horizontal position of the quad stimulus as a fraction the total display width.")
    location_y: float = Field(default=-1.0, ge=0, le=1, description="Vertical position of the quad stimulus as a fraction of the total display height.")


class RandomFlip(BaseSchema):
    """Configuration for the random ON/OFF flip timing of a visual stimulus."""

    quad_time_lower_bound: float = Field(
        default=0.2, description="Lower bound (s) of the uniform distribution for quad flip timing."
    )
    quad_time_upper_bound: float = Field(
        default=0.5, description="Upper bound (s) of the uniform distribution for quad flip timing."
    )
