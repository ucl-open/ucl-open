from pydantic import Field
from swc.aeon.schema import BaseSchema


class SerialDevice(BaseSchema):
    """Represents a serial communication device."""

    port_name: str = Field(examples=["COMx"], description="The name of the device serial port.")
    baud_rate: int = Field(default=9600, description="Baud rate for serial communication.")
    new_line: str = Field(
        default="\r\n", description="Line termination sequence used to delimit incoming messages."
    )
    read_buffer_size: int = Field(default=4096, description="Size, in bytes, of the read buffer.")
    write_buffer_size: int = Field(default=2048, description="Size, in bytes, of the write buffer.")
