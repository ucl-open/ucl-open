from typing import List
from pydantic import Field
from swc.aeon.schema import BaseSchema
from ucl_open.devices.harp import HarpBehavior
from ucl_open.core.base import UShort


class CameraController(BaseSchema):
    """Represents a CameraController module on a BehaviorBoard device."""

    trigger_frequency: int = Field(
        examples=["50"],
        description="The frequency, in Hz, at which to emit camera triggers from DO0 of a behavior board (`CameraOutput0`)",
    )


class PulseWidths(BaseSchema):
    pulse_do1: UShort = Field(alias="PulseDO1")
    pulse_do2: UShort = Field(alias="PulseDO2")
    pulse_do3: UShort = Field(alias="PulseDO3")


class PulseController(BaseSchema):
    """
    Represents the PulseController module on the BehaviourBoard.
    Mirrors the externalized properties of the Bonsai workflow of the same name,
    excluding subject name properties.
    """

    output_pulse_enable: List[str] = Field(
        default_factory=lambda: ["DO1", "DO2", "DO3"],
        description="List of digital output lines that are enabled for pulse generation.",
    )
    pulse_widths: PulseWidths = Field(description="Pulse width configuration for DO1, DO2, and DO3 lines.")


class RunningWheelModule(BaseSchema):
    """Represents the RunningWheel Bonsai workflow module.
    Exposes wheel geometry parameters used to compute speed and distance from encoder counts.
    """

    counts_per_rev: int = Field(
        description="Number of encoder counts per full revolution of the running wheel."
    )
    wheel_diameter_mm: float = Field(description="The diameter, in millimeters, of the running wheel.")


class BehaviorBoard(HarpBehavior):
    """Represents a Harp Behavior Board device."""

    pulse_controller: PulseController | None = Field(
        default=None, description="Optional PulseController module for generating digital output pulses."
    )
    camera_controller: CameraController | None = Field(
        default=None, description="Optional CameraController module for emitting camera trigger pulses."
    )
    running_wheel: RunningWheelModule | None = Field(
        default=None, description="Optional RunningWheelModule module to define wheel geometry."
    )
