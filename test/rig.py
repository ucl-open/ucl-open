from pydantic import Field

from ucl_open.core.base import BaseSchema
import ucl_open.devices as Device
from ucl_open.video import Camera
from ucl_open.vision import SyncQuad, RandomFlip, Screen


class TestRig(BaseSchema):
    behavior_board: Device.BehaviorBoard = Field(description="Harp Behavior Board with optional controller modules.")
    camera: Camera = Field(description="Discriminated camera configuration supporting Arducam or Spinnaker devices.")
    arduino: Device.ArduinoDevice = Field(description="Arduino serial device specifying the sampling interval for analog and I2C measurements.")
    serial_device: Device.SerialDeviceModule = Field(description="SerialDevice workflow module with port, framing, and buffer configuration.")
    screen: Screen = Field(description="Visual stimulus display with render/update frequencies, texture assets, and calibration parameters.")
    sync_quad: SyncQuad = Field(description="Synchronisation quad stimulus defining the extent and position of a small reference visual.")
    random_flip: RandomFlip = Field(description="Random ON/OFF flip timing for a visual stimulus with uniform distribution bounds.")
