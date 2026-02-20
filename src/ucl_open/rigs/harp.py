from typing import ClassVar
from pydantic import Field
from ucl_open.rigs.base import Device


class HarpDevice(Device):
    who_am_i: ClassVar[int] = Field(description="The unique identifier for the device type.")
    port_name: str = Field(examples=["COM"], description="The name of the device serial port.")


class HarpClockSynchronizer(HarpDevice):
    device_type: ClassVar[str] = "HarpClockSynchronizer"
    who_am_i: ClassVar[int] = 1152


class HarpTimestampGeneratorGen3(HarpDevice):
    device_type: ClassVar[str] = "HarpTimestampGeneratorGen3"
    who_am_i: ClassVar[int] = 1158


class HarpCameraControllerGen2(HarpDevice):
    device_type: ClassVar[str] = "HarpCameraControllerGen2"
    who_am_i: ClassVar[int] = 1170


class HarpBehavior(HarpDevice):
    device_type: ClassVar[str] = "HarpBehavior"
    who_am_i: ClassVar[int] = 1216