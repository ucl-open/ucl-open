from typing import List
from pydantic import Field
from swc.aeon.schema import BaseSchema
from ucl_open.devices.harp import HarpBehavior
from ucl_open.core.base import UShort


class CameraTriggerController(BaseSchema):
    """Represents a CameraTriggerController module on a BehaviorBoard device."""

    trigger0_frequency: int = Field(
        examples=["50"],
        description="The frequency, in Hz, at which to emit camera triggers on Trigger0 (DO0, CameraOutput0)",
    )
    trigger1_frequency: int = Field(
        examples=["50"],
        description="The frequency, in Hz, at which to emit camera triggers on Trigger1 (DO1, CameraOutput1)",
    )


class PulseWidths(BaseSchema):
    pulse_do1: UShort = Field(alias="PulseDO1")
    pulse_do2: UShort = Field(alias="PulseDO2")
    pulse_do3: UShort = Field(alias="PulseDO3")


class PulseController(BaseSchema):
    """Represents the PulseController module on the BehaviorBoard."""

    active_pulses: List[str] = Field(
        default_factory=lambda: ["DO1", "DO2", "DO3"],
        description="List of digital output lines that are enabled for pulse generation.",
    )
    pulse_widths: PulseWidths = Field(description="Pulse width configuration for DO1, DO2, and DO3 lines.")


class RunningWheel(BaseSchema):
    """Represents configuration parameters of the RunningWheel module.
    Exposes wheel geometry parameters used to compute speed and distance from encoder counts.
    """

    counts_per_revolution: int = Field(
        description="Number of encoder counts per full revolution of the running wheel."
    )
    wheel_diameter: float = Field(description="The diameter of the running wheel, in metric units.")


class BehaviorBoard(HarpBehavior):
    """Represents a Harp Behavior Board device."""

    pulse_controller: PulseController | None = Field(
        default=None, description="Optional PulseController module for generating digital output pulses."
    )
    camera_trigger_controller: CameraTriggerController | None = Field(
        default=None, description="Optional CameraTriggerController module for emitting camera trigger pulses."
    )
    running_wheel: RunningWheel | None = Field(
        default=None, description="Optional RunningWheelModule module to define wheel geometry."
    )
