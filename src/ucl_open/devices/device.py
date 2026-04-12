from typing import ClassVar, Dict, Literal
from pydantic import Field
from ucl_open.devices.harp import HarpDevice
from swc.aeon.schema import BaseSchema
import ucl_open.core.base as data_types


class StepperPositions(BaseSchema):
    """
    Absolute target position for the 5-axis spout rig, expressed in task-relative axes.
    """

    left_elevation: int = Field(
        description="Left spout elevation axis absolute position (steps). Maps to motor 1"
    )
    right_elevation: int = Field(
        description="Right spout elevation axis absolute position (steps). Maps to motor 2"
    )
    right_radial: int = Field(
        description="Right spout radial axis (in/out) absolute position (steps). Maps to motor 3"
    )
    left_radial: int = Field(
        description="Left spout radial axis (in/out) absolute position (steps). Maps to motor 4"
    )
    base_transverse: int = Field(
        description="Base transverse axis absolute position (steps). Maps to motor 5"
    )


class SpoutRigPosition(BaseSchema):
    """
    Dictionary of named absolute positions, e.g.:
      home, both_in, both_out
    """

    positions: Dict[str, StepperPositions] = Field(
        default_factory=dict,
        description="Named absolute positions of the lick spout stage stepper rig, keyed by a string identifier.",
        examples=[
            {
                "home": {
                    "left_elevation": 0,
                    "right_elevation": 0,
                    "right_radial": 0,
                    "left_radial": 0,
                    "base_transverse": 0,
                },
                "both_in": {
                    "left_elevation": 1000,
                    "right_elevation": 1000,
                    "right_radial": 2000,
                    "left_radial": 2000,
                    "base_transverse": 500,
                },
                "both_out": {
                    "left_elevation": 1000,
                    "right_elevation": 1000,
                    "right_radial": 1000,
                    "left_radial": 1000,
                    "base_transverse": 500,
                },
            }
        ],
    )


class SerialDevice(BaseSchema):
    """Represents a serial communication device."""

    port_name: str = Field(examples=["COMx"], description="The name of the device serial port.")
    baud_rate: int = Field(default=9600, description="Baud rate for serial communication.")
    new_line: str = Field(
        default="\r\n", description="Line termination sequence used to delimit incoming messages."
    )
    read_buffer_size: int = Field(default=4096, description="Size, in bytes, of the read buffer.")
    write_buffer_size: int = Field(default=2048, description="Size, in bytes, of the write buffer.")


class LicketySplit(HarpDevice):
    """Represents a Harp LicketySplit device."""

    device_type: Literal["LicketySplit"] = "LicketySplit"
    who_am_i: ClassVar[int] = 1400
    channel0_trigger_threshold: data_types.UShort = Field(
        default=0, description="ADC threshold above which Channel 0 triggers a lick"
    )
    channel0_untrigger_threshold: data_types.UShort = Field(
        default=0, description="ADC threshold below which Channel 0 untriggers a lick"
    )


class LickSpoutStageDriver(SerialDevice):
    """Represents an Arduino device driving stepper motors controlling a lick spout stage."""

    device_type: Literal["LickSpoutStageDriver"] = "LickSpoutStageDriver"

    # Protocol command bytes
    move: data_types.Byte = Field(default=71, description="Command byte for MOVE.")
    set_speed: data_types.Byte = Field(default=72, description="Command byte for SET SPEED.")
    set_acceleration: data_types.Byte = Field(
        default=73, description="Command byte for SET ACCELERATION."
    )

    # Motion parameters
    speed: int = Field(default=300, description="Default motor speed.")
    acceleration_major: int = Field(default=20, description="Major acceleration component.")
    acceleration_minor: int = Field(default=2, description="Minor acceleration component.")

    # Set positions
    set_position: SpoutRigPosition
