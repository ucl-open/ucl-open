from pydantic import Field, RootModel
from pydantic.json_schema import JsonSchemaValue
from swc.aeon.schema import BaseSchema
from ucl_open.devices.harp import HarpBehavior
from ucl_open.core.base import UShort, bind_typename


class DigitalOutputs(RootModel[str]):
    """A set of behavior board digital output lines, written comma separated."""

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler) -> JsonSchemaValue:
        """Binds the device's own flags enum, so generated properties can be assigned it."""
        return bind_typename(handler(core_schema), "Harp.Behavior.DigitalOutputs")


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
    """Pulse durations for the behavior board digital outputs, in milliseconds.

    A line that is not used on a rig may be omitted.
    """

    pulse_do1: UShort = Field(alias="PulseDO1", description="Pulse duration on DO1, in milliseconds.")
    pulse_do2: UShort = Field(alias="PulseDO2", description="Pulse duration on DO2, in milliseconds.")
    pulse_do3: UShort = Field(
        default=0, alias="PulseDO3", description="Pulse duration on DO3, in milliseconds."
    )


class PulseController(BaseSchema):
    """Represents the PulseController module on the BehaviorBoard."""

    output_pulse_enable: DigitalOutputs = Field(
        default="DO1, DO2, DO3",
        description="Digital output lines enabled for pulse generation, comma separated.",
    )
    pulse_widths: PulseWidths = Field(description="Pulse width configuration for DO1, DO2, and DO3 lines.")


class RunningWheel(BaseSchema):
    """Represents configuration parameters of the RunningWheel module.
    Exposes wheel geometry parameters used to compute speed and distance from encoder counts.
    """

    counts_per_rev: int = Field(
        description="Number of encoder counts per full revolution of the running wheel."
    )
    wheel_diameter_mm: float = Field(description="The diameter of the running wheel, in millimetres.")


class BehaviorBoard(HarpBehavior):
    """Represents a Harp Behavior Board device."""

    pulse_controller: PulseController | None = Field(
        default=None, description="Optional PulseController module for generating digital output pulses."
    )
    camera_trigger_controller: CameraTriggerController | None = Field(
        default=None,
        description="Optional CameraTriggerController module for emitting camera trigger pulses.",
    )
    running_wheel: RunningWheel | None = Field(
        default=None, description="Optional RunningWheelModule module to define wheel geometry."
    )
