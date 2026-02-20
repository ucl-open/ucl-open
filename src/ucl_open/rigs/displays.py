# TODO - this should live in ucl-open general definitions

# Import core types
from typing import Literal
from pydantic import Field
import ucl_open.rigs.data_types as Types

from ucl_open.rigs.base import BaseSchema, Device

class DisplayIntrinsics(BaseSchema):
    frame_width: int = Field(default=1920, ge=0, description="Frame width (px)")
    frame_height: int = Field(default=1080, ge=0, description="Frame height (px)")
    display_width: float = Field(default=20, ge=0, description="Display width (cm)")
    display_height: float = Field(default=15, ge=0, description="Display width (cm)")

class DisplayExtrinsics(BaseSchema):
    rotation: Types.Vector3 = Field(
        default=Types.Vector3(x=0.0, y=0.0, z=0.0), description="Rotation vector (radians)", validate_default=True
    )
    translation: Types.Vector3 = Field(
        default=Types.Vector3(x=0.0, y=1.309016, z=-13.27), description="Translation (in cm)", validate_default=True
    )

class DisplayCalibration(BaseSchema):
    intrinsics: DisplayIntrinsics = Field(default=DisplayIntrinsics(), description="Intrinsics", validate_default=True)
    extrinsics: DisplayExtrinsics = Field(default=DisplayExtrinsics(), description="Extrinsics", validate_default=True)