from typing import Dict
from pydantic import Field
import ucl_open.core.base as Types

from swc.aeon.schema import BaseSchema


class DisplayIntrinsics(BaseSchema):
    frame_width: int = Field(default=1920, ge=0, description="Pixel frame width")
    frame_height: int = Field(default=1080, ge=0, description="Pixel frame height")
    display_width: float = Field(default=20, ge=0, description="Physical display width")
    display_height: float = Field(default=15, ge=0, description="Physical display height")


class DisplayExtrinsics(BaseSchema):
    rotation: Types.Vector3 = Field(
        description="Euler rotation vector (radians)"
    )
    translation: Types.Vector3 = Field(
        description="Translation vector"
    )


class DisplayCalibration(BaseSchema):
    intrinsics: DisplayIntrinsics = Field(
        default=DisplayIntrinsics(), description="Intrinsics", validate_default=True
    )
    extrinsics: DisplayExtrinsics = Field(
        default=DisplayExtrinsics(), description="Extrinsics", validate_default=True
    )


class Screen(BaseSchema):
    display_index: int = Field(default=1, description="Display index")
    target_render_frequency: float = Field(default=60, description="Target render frequency")
    target_update_frequency: float = Field(default=120, description="Target update frequency")
    texture_assets_directory: str = Field(default="Textures", description="Calibration directory")
    calibration: Dict[str, DisplayCalibration] | None = Field(
        default=None,
        description="Calibration parameters for a set of named display monitors for visual stimuli",
    )
    brightness: float = Field(default=0, le=1, ge=-1, description="Brightness")
    contrast: float = Field(default=1, le=1, ge=-1, description="Contrast")
