from typing import ClassVar, Literal
from pydantic import Field
from ucl_open.devices.harp import HarpDevice
from swc.aeon.schema import BaseSchema
import ucl_open.core.base as data_types
import ucl_open.devices.data_types as device_data_types


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
    accel_major: int = Field(default=20, description="Major acceleration component.")
    accel_minor: int = Field(default=2, description="Minor acceleration component.")

    # Set positions
    set_positions: device_data_types.SpoutRigPosition
