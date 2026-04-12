from typing import ClassVar, Literal
from pydantic import Field
from ucl_open.devices.harp import HarpDevice
import ucl_open.core.base as data_types


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
