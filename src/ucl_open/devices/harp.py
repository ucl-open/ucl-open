from typing import ClassVar
from pydantic import Field
from swc.aeon.schema import BaseSchema


class HarpDevice(BaseSchema):
    who_am_i: ClassVar[int] = Field(description="The unique identifier for the device type.")
    port_name: str = Field(examples=["COM"], description="The name of the device serial port.")


class HarpClockSynchronizer(HarpDevice):
    who_am_i: ClassVar[int] = 1152


class HarpTimestampGeneratorGen3(HarpDevice):
    """Harp Timestamp Generator Gen3 (who_am_i=1158). Provides hardware clock synchronisation."""

    who_am_i: ClassVar[int] = 1158
    timer_frequency: Literal["Disabled", "Timer50Hz", "Timer100Hz", "Timer200Hz", "Timer500Hz", "Timer1000Hz"] = Field(
        default="Timer1000Hz",
        description="Frequency of the timer output signal.",
    )


class HarpCameraControllerGen2(HarpDevice):
    who_am_i: ClassVar[int] = 1170


class HarpBehavior(HarpDevice):
    who_am_i: ClassVar[int] = 1216


class HarpHobgoblin(HarpDevice):
    who_am_i: ClassVar[int] = 123
