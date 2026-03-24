from typing import Dict
from pydantic import Field
from swc.aeon.schema import BaseSchema


class StepperPositions(BaseSchema):
    """
    Absolute target position for the 5-axis spout rig, expressed in task-relative axes.
    """

    left_elevation: int = Field(
        description="Left spout elevation axis absolute position (steps). Maps to motor 1"
    )
    right_elevation: int = Field(
        description="Right spout elevation axis absolute position (steps). Maps to motor 2"
    )
    right_radial: int = Field(
        description="Right spout radial axis (in/out) absolute position (steps). Maps to motor 3"
    )
    left_radial: int = Field(
        description="Left spout radial axis (in/out) absolute position (steps). Maps to motor 4"
    )
    base_transverse: int = Field(
        description="Base transverse axis absolute position (steps). Maps to motor 5"
    )


class SpoutRigPosition(BaseSchema):
    """
    Dictionary of named absolute positions, e.g.:
      home, both_in, both_out
    """

    positions: Dict[str, StepperPositions] = Field(
        default_factory=dict,
        description="Named absolute positions of the lick spout stage stepper rig, keyed by a string identifier.",
        examples=[
            {
                "home": {
                    "left_elevation": 0,
                    "right_elevation": 0,
                    "right_radial": 0,
                    "left_radial": 0,
                    "base_transverse": 0,
                },
                "both_in": {
                    "left_elevation": 1000,
                    "right_elevation": 1000,
                    "right_radial": 2000,
                    "left_radial": 2000,
                    "base_transverse": 500,
                },
                "both_out": {
                    "left_elevation": 1000,
                    "right_elevation": 1000,
                    "right_radial": 1000,
                    "left_radial": 1000,
                    "base_transverse": 500,
                },
            }
        ],
    )
