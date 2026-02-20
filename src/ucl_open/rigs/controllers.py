from typing import ClassVar, Literal, List
from pydantic import Field
from ucl_open.rigs.base import BaseSchema
from ucl_open.rigs.data_types import UShort 

class CameraController(BaseSchema):
    """Represents a CameraController Module for a BehaviourBoard device.
    Mirrors the externalized properties of the Bonsai workflow of the same name,
    excluding subject name properties.
    """
    trigger_frequency: int = Field(examples=["50"], description="The frequency, in Hz, at which to emit camera triggers from DO0 of a behavior board (`CameraOutput0`)")

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

    output_pulse_enable: List[str] = Field(default_factory=lambda: ["DO1", "DO2", "DO3"], description="List of digital output lines that are enabled for pulse generation.")
    pulse_widths: PulseWidths = Field(description="Pulse width configuration for DO1, DO2, and DO3 lines.")

class RunningWheelModule(BaseSchema):
    """Represents the RunningWheel Bonsai workflow module.
    Exposes wheel geometry parameters used to compute speed and distance from encoder counts.
    """
    counts_per_rev: int = Field(description="Number of encoder counts per full revolution of the running wheel.")
    wheel_diameter_mm: float = Field( description="The diameter, in millimeters, of the running wheel.")

class LedController(BaseSchema):
    """Specifies the digital pin to control a single LED"""
    digital_out_pin: int = Field(description="The digital output pin for this LED driver")