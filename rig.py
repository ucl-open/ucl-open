from typing import Dict
from pydantic import Field

from ucl_open.rigs.base import BaseSchema
import ucl_open.rigs.device as Device
from ucl_open.rigs.video import Camera

class TestRig(BaseSchema):
    behavior_boards: Dict[str, Device.BehaviorBoard] = Field(description="Mapping from logical names to BehaviorBoard devices (e.g. 'main', 'aux').")
    cameras: Dict[str, Camera] = Field(description="Mapping from camera role names to camera configurations (e.g. 'body', 'face', 'top').")
    arduinos: Dict[str, Device.ArduinoDevice] | None = Field(default=None,description="Optional mapping from logical names to Arduino devices used in the dome (e.g. for LED drivers or other IO).")
    serial_devices: Dict[str, Device.SerialDeviceModule] | None = Field(default=None,description="Optional mapping from logical names to auxiliary serial devices used in the dome.")
    screen: Device.Screen
