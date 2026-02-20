from typing import ClassVar, Literal, Dict
from pydantic import Field
from ucl_open.rigs.base import Device
import ucl_open.rigs.data_types as data_types
from ucl_open.rigs.harp import HarpDevice, HarpBehavior
import ucl_open.rigs.controllers as Controllers
import ucl_open.rigs.displays as Displays

class SerialDevice(Device):
    """A base class for creating serial device models."""
    device_type: Literal["SerialDevice"] = "SerialDevice"
    port_name: str = Field(examples=["COMx"], description="The name of the device serial port.")
    baud_rate: int = Field(default=9600, description="Baud rate for serial communication.")

class SerialDeviceModule(SerialDevice):
    """Represents the SerialDevice workflow module.

    Mirrors all externalized properties of SerialDevice.bonsai, including
    port configuration, framing and buffer settings.
    """
    new_line: str = Field(default="\r\n", description="Line termination sequence used to delimit incoming messages.")
    read_buffer_size: int = Field(default=4096, description="Size, in bytes, of the read buffer.")
    write_buffer_size: int = Field(default=2048, description="Size, in bytes, of the write buffer.")

class LicketySplit(HarpDevice):
    """Represents a Harp LicketySplit device."""
    device_type: Literal["LicketySplit"] = "LicketySplit"
    who_am_i: ClassVar[int] = 1400
    channel0_trigger_threshold: data_types.UShort = Field(
        default=0,
        description="ADC threshold above which Channel 0 triggers a lick"
    )
    channel0_untrigger_threshold: data_types.UShort = Field(
        default=0,
        description="ADC threshold below which Channel 0 untriggers a lick"
    )

class BehaviorBoard(HarpBehavior):
    """Represents a Harp Behavior Board device."""
    device_type: Literal["BehaviorBoard"] = "BehaviorBoard"
    pulse_controller: Controllers.PulseController | None = Field(default=None, description="Optional PulseController module for generating digital output pulses.")
    camera_controller: Controllers.CameraController | None = Field(default=None, description="Optional CameraController module for emitting camera trigger pulses.")
    running_wheel: Controllers.RunningWheelModule | None = Field(default=None, description="Optional RunningWheelModule module to define wheel geometry.")

class ArduinoDevice(SerialDevice):
    """Represents a base class for Arduino serial devices used in Bonsai workflows."""
    sampling_interval: int = Field(description="Sampling interval, in milliseconds, between analog and I2C measurements.")

class LedDriver(ArduinoDevice):
    """Represents an Arduino device used to drive LEDs."""
    device_type: Literal["LedDriver"] = "LedDriver"
    led_controller: Controllers.LedController = Field(description="LedController module for generating digital output pulses.")

class LickSpoutStageDriver(SerialDeviceModule):
    """Represents an Arduino device driving stepper motors controlling a lick spout stage."""
    device_type: Literal["LickSpoutStageDriver"] = "LickSpoutStageDriver"
    
     # Protocol command bytes
    byte_move: data_types.Byte = Field(default=71, description="Command byte for MOVE.")
    byte_set_speed: data_types.Byte = Field(default=72, description="Command byte for SET SPEED.")
    byte_set_acceleration: data_types.Byte = Field(default=73, description="Command byte for SET ACCELERATION.")
    
    # Motion parameters
    speed: int = Field(default=300, description="Default motor speed.")
    accel_major: int = Field(default=20, description="Major acceleration component.")
    accel_minor: int = Field(default=2, description="Minor acceleration component.")

    # Set positions
    set_positions: data_types.SpoutRigPosition 

class Screen(Device):
    device_type: Literal["Screen"] = Field(default="Screen", description="Device type")
    display_index: int = Field(default=1, description="Display index")
    target_render_frequency: float = Field(default=60, description="Target render frequency")
    target_update_frequency: float = Field(default=120, description="Target update frequency")
    texture_assets_directory: str = Field(default="Textures", description="Calibration directory")
    calibration: Dict[str, Displays.DisplayCalibration] | None = Field(default=None,description="Calibration parameters for a set of named display monitors for visual stimuli")
    brightness: float = Field(default=0, le=1, ge=-1, description="Brightness")
    contrast: float = Field(default=1, le=1, ge=-1, description="Contrast")