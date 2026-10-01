from datetime import datetime
from typing import List

from pydantic import Field
from swc.aeon.schema import BaseSchema

import ucl_open.core.base as data_types
from ucl_open.core.artefacts import ArtefactPath


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
    payload_path: ArtefactPath | None = Field(
        default=None,
        description="Relative path of a file a consumer still needs alongside the points, such as a gamma LUT bitmap.",
    )
