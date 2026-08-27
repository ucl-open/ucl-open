from pydantic import Field
from swc.aeon.schema import BaseSchema

import ucl_open.core.base as data_types
from ucl_open.components.outputs import DigitalOutput


class ValveCalibrationPoint(BaseSchema):
    """A single measured point relating valve open time to delivered volume."""

    open_time: data_types.Double = Field(gt=0, description="Valve open time, in milliseconds.")
    volume: data_types.Double = Field(ge=0, description="Measured delivered volume, in microliters.")


class ValveCalibration(BaseSchema):
    """A valve calibration measurement set with an optional linear fit."""

    points: list[ValveCalibrationPoint] = Field(
        default_factory=list, description="Measured open-time/volume calibration points."
    )
    slope: data_types.Double | None = Field(
        default=None, description="Fitted slope of the open-time to volume relationship, in uL/ms."
    )
    intercept: data_types.Double | None = Field(
        default=None, description="Fitted intercept of the open-time to volume relationship, in uL."
    )


class RewardValve(BaseSchema):
    """A liquid-reward solenoid valve driven by a digital output line."""

    open_time: data_types.Double = Field(
        gt=0, description="Calibrated valve open time delivering the target reward volume, in milliseconds."
    )
    output: DigitalOutput = Field(description="The digital output driving this valve.")
    calibration: ValveCalibration | None = Field(
        default=None, description="Calibration measurements this valve's open time was derived from."
    )
