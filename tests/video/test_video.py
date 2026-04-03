import pytest
from pydantic import Field, ValidationError
from typing import Dict, List
from ucl_open.video import Camera, ArducamOV9180, SpinnakerCamera
from ucl_open.core.rig import Rig
from ucl_open.core import DiscriminatorTypeMixin
from swc.aeon.schema import BaseSchema

class CameraRig(Rig):
    cameras: Dict[str, Camera]

class ExcludedDevice(DiscriminatorTypeMixin, BaseSchema):
    test_parameter: int = Field(default=0)

@pytest.mark.parametrize(
    ("klass", "parameter", "expected"), 
    [
        (CameraRig, {"spinnaker": SpinnakerCamera(), "arducam": ArducamOV9180()}, ["spinnaker", "SpinnakerCamera"]),
        (CameraRig, {"spinnaker": SpinnakerCamera(), "arducam": ArducamOV9180()}, ["arducam", "ArducamOV9180"])
    ]
)
def test_camera_discriminator(klass: type[CameraRig], parameter: Dict[str, Camera], expected: List[str]):
    inst = klass(root_path="", cameras=parameter)
    json_str = inst.model_dump_json()
    deserialized = klass.model_validate_json(json_str)
    assert deserialized.cameras[expected[0]].root.discriminator_type == expected[1]
    
@pytest.mark.parametrize(
    ("klass", "parameter", "expected"), 
    [
        (CameraRig, {"spinnaker": SpinnakerCamera(), "arducam": ArducamOV9180(), "excluded": ExcludedDevice()}, "")
    ]
)
def test_camera_exclusion(klass: type[CameraRig], parameter: Dict[str, Camera], expected: str):
    with pytest.raises(ValidationError):
        klass(root_path="", cameras=parameter)