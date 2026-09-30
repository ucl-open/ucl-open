from datetime import datetime
from typing import Dict, List

from pydantic import Field
from swc.aeon.schema import BaseSchema

import ucl_open.core.base as data_types


class Calibration(BaseSchema):
    """Provenance shared by every calibration artefact."""

    calibrated_at: datetime = Field(description="When the calibration was measured, in UTC.")
    calibrated_by: str = Field(description="Who ran the calibration.")
    machine_name: str = Field(description="Name of the machine the calibration was measured on.")
    notes: str = Field(default="", description="Free-text notes about the calibration.")


class CalibrationPoint(BaseSchema):
    """One measured pair of a calibration curve."""

    x: data_types.Double = Field(description="The value the rig controls, in the unit of the x axis.")
    y: data_types.Double = Field(description="The measured value, in the unit of the y axis.")


class CalibrationCurve(Calibration):
    """A calibration measured as pairs, such as valve opening time against delivered volume."""

    x_name: str = Field(examples=["pulse_width"], description="Name of the quantity the rig controls.")
    x_unit: str = Field(examples=["ms"], description="Unit of the x values.")
    y_name: str = Field(examples=["volume"], description="Name of the measured quantity.")
    y_unit: str = Field(examples=["ul"], description="Unit of the y values.")
    points: List[CalibrationPoint] = Field(
        min_length=2, description="Measured pairs; the fit is done at load, not stored."
    )
    payload_path: str | None = Field(
        default=None,
        description="Relative path of a file a consumer still needs alongside the points, such as a gamma LUT bitmap.",
    )


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
