from typing import Dict
from pydantic import Field
import ucl_open.core.base as Types

from swc.aeon.schema import BaseSchema


class ViewportConfiguration(BaseSchema):
    width: float = Field(default=1, ge=0, le=0, description="The width of the viewport as a fraction of total screen width")
    height: float = Field(default=1, ge=0, le=0, description="The height of the viewport as a fraction of total screen width")
    x: float = Field(default=0, ge=0, le=0, description="The x-coordinate of the lower left corner of the viewport as a fraction of total screen width")
    y: float = Field(default=0, ge=0, le=0, description="The y-coordinate of the lower left corner of the viewport as a fraction of total screen height")


class DisplayIntrinsics(BaseSchema):
    viewport_configuration: ViewportConfiguration = Field(default = ViewportConfiguration(), description="The viewport configuration for this display intrinsic")
    display_width: float = Field(default=20, ge=0, description="Physical display width")
    display_height: float = Field(default=15, ge=0, description="Physical display height")


class DisplayExtrinsics(BaseSchema):
    rotation: Types.Vector3 = Field(
        default=Types.Vector3(x=0, y=0, z=0), description="Euler rotation vector (radians)"
    )
    translation: Types.Vector3 = Field(
        default=Types.Vector3(x=0, y=0, z=0), description="Translation vector"
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
    window_width: int = Field(default=1920, ge=0, description="Width of the screen in pixels")
    window_height: int = Field(default=1080, ge=0, description="Height of the screen in pixels")
    target_render_frequency: float = Field(default=60, description="Target render frequency")
    target_update_frequency: float = Field(default=120, description="Target update frequency")
    texture_assets_directory: str = Field(default="Textures", description="Calibration directory")
    calibration: Dict[str, DisplayCalibration] | None = Field(
        default=None,
        description="Calibration parameters for a set of named display monitors for visual stimuli",
    )
    brightness: float = Field(default=0, le=1, ge=-1, description="Brightness")
    contrast: float = Field(default=1, le=1, ge=-1, description="Contrast")
