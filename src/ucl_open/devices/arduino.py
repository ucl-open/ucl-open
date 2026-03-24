from pydantic import Field
from ucl_open.core import BaseSchema
from ucl_open.devices.device import SerialDevice


class ArduinoDevice(SerialDevice):
    """Represents a base class for Arduino serial devices used in Bonsai workflows."""

    sampling_interval: int = Field(
        description="Sampling interval, in milliseconds, between analog and I2C measurements."
    )


class LedController(BaseSchema):
    """Specifies the digital pin to control a single LED"""

    digital_out_pin: int = Field(description="The digital output pin for this LED driver")


class LedDriver(ArduinoDevice):
    """Represents an Arduino device used to drive LEDs."""

    led_controller: LedController = Field(
        description="LedController module for generating digital output pulses."
    )
