from enum import StrEnum
import json
from pathlib import Path
from typing import Annotated, Generic, TypeVar, Any, Dict
from pydantic import Field
from ucl_open.rigs.base import BaseSchema

SByte = Annotated[int, Field(ge=-128, le=127)]
Byte = Annotated[int, Field(ge=0, le=255)]
Short = Annotated[int, Field(ge=-32768, le=32767)]
UShort = Annotated[int, Field(ge=0, le=65535)]
Int = Annotated[int, Field(ge=-2147483648, le=2147483647)]
UInt = Annotated[int, Field(ge=0, le=4294967295)]
Long = Annotated[int, Field(ge=-9223372036854775808, le=9223372036854775807)]
ULong = Annotated[int, Field(ge=0, le=18446744073709551615)]

Float = float
Double = float
String = str
Bool = bool

class TimestampSource(StrEnum):
    NULL = "null"
    HARP = "harp"
    RENDER = "render"
    ARDUINO = "arduino"

TData = TypeVar("TData", bound=Any)

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
                "home": {"left_elevation": 0, "right_elevation": 0, "right_radial": 0, "left_radial": 0, "base_transverse": 0},
                "both_in": {"left_elevation": 1000, "right_elevation": 1000, "right_radial": 2000, "left_radial": 2000, "base_transverse": 500},
                "both_out": {"left_elevation": 1000, "right_elevation": 1000, "right_radial": 1000, "left_radial": 1000, "base_transverse": 500},
            }
        ],
    )

class Vector3(BaseSchema):
    x: float = Field(description="X coordinate of the point.")
    y: float = Field(description="Y coordinate of the point.")
    z: float = Field(description="Z coordinate of the point.")

class SoftwareEvent(BaseSchema, Generic[TData]):
    """
    A software event is a generic event that can be used to track any event that occurs in the software.
    """
    name: str = Field(..., description="The name of the event.")
    timestamp: float | None = Field(default=None, description="The timestamp of the event.")
    timestamp_source: TimestampSource = Field(default=TimestampSource.NULL,description="The source of the timestamp. Typically either a harp device or on the visual render loop")
    frame_index: int | None = Field(default=None,ge=0,description="The frame index of the event.")
    frame_timestamp: float | None = Field(default=None,description="The timestamp of the frame.")
    data: TData | None = Field(default=None,description="The data payload of the event.")

class DataTypes(BaseSchema):
    vector3 : Vector3 
    software_event : SoftwareEvent
    spout_rig_position: SpoutRigPosition

def main() -> None:
    schema = DataTypes.model_json_schema(union_format="primitive_type_array")
    schema.pop("properties", None)
    Path("DataTypes.json").write_text(json.dumps(schema, indent=2))