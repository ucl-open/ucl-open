from typing import Dict

from pydantic import Field
from swc.aeon.schema import BaseSchema

import ucl_open.core.base as data_types
from ucl_open.core.calibration import Calibration


class MeshMap(Calibration):
    """A projection mesh map, stored as a file beside this descriptor."""

    azimuth_resolution: data_types.Int = Field(gt=0, description="Number of mesh points in azimuth.")
    elevation_resolution: data_types.Int = Field(gt=0, description="Number of mesh points in elevation.")
    mesh_path: str = Field(description="Relative path of the mesh CSV that BonVision loads.")


class SpeakerFilters(Calibration):
    """Per-speaker equalisation filters, each stored as a file beside this descriptor."""

    filters: Dict[str, str] = Field(
        description="Relative path of the FIR filter file, keyed by speaker key in the speaker array."
    )


class CalibrationFiles(BaseSchema):
    """Calibration artefacts of a rig that are not tied to a pulsed output line.

    Paths are relative to the rig's configuration directory.
    """

    gamma: str | None = Field(
        default=None, examples=["calibration/gamma.json"], description="Relative path of the gamma CalibrationCurve."
    )
    mesh_map: str | None = Field(
        default=None, examples=["calibration/mesh.json"], description="Relative path of the MeshMap descriptor."
    )
    speaker_filters: str | None = Field(
        default=None,
        examples=["calibration/speaker-filters.json"],
        description="Relative path of the SpeakerFilters descriptor.",
    )


class ProjectionCalibration(BaseSchema):
    """File-based calibration assets for mesh-mapped projection displays.

    Superseded by CalibrationFiles; kept until av-dome migrates (ucl-open/av-dome#20).
    """

    mesh_map_path: str = Field(
        examples=["C:\\RigConfigs\\MeshMap.csv"],
        description="Path to the mesh-mapping interpolation file (CSV)",
    )
    gamma_lut_path: str = Field(
        examples=["C:\\RigConfigs\\gammalut.bmp"],
        description="Path to the gamma lookup-table image (BMP)",
    )
