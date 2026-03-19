import os
import sys
from pathlib import Path

from pydantic_yaml import to_yaml_str
from ucl_open.core.base import BaseSchema
from ucl_open.core.experiment import Experiment
from ucl_open.core.task import Task, TaskParameters
import ucl_open.devices as Device
from ucl_open.video import Camera, SpinnakerCamera
from ucl_open.vision import SyncQuad, RandomFlip, Screen
from aind_behavior_services.utils import BonsaiSgenSerializers, convert_pydantic_to_bonsai
from pydantic import Field

sys.path.insert(0, os.path.dirname(__file__))
from rig import TestRig


class TestExperiment(BaseSchema):
    """Unified experiment schema combining rig, task, and session."""
    rig: TestRig = Field(description="Rig hardware configuration.")
    task: Task = Field(description="Task logic and parameters.")
    session: Experiment = Field(description="Session metadata.")


experiment = TestExperiment(
    rig=TestRig(
        behavior_board=Device.BehaviorBoard(port_name="COM3"),
        camera=Camera(SpinnakerCamera()),
        arduino=Device.ArduinoDevice(port_name="COM4", baud_rate=1000000, sampling_interval=10),
        serial_device=Device.SerialDeviceModule(port_name="COM5"),
        screen=Screen(),
        sync_quad=SyncQuad(),
        random_flip=RandomFlip(),
    ),
    task=Task(task_parameters=TaskParameters()),
    session=Experiment(
        workflow="main.bonsai",
        commit="",
        repository_url="https://github.com/ucl-open/rigs",
    ),
)


def main(output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # YAML instance — runtime config for Bonsai
    yml_path = output_path / "TestExperiment.yml"
    yml_path.write_text(to_yaml_str(experiment))

    # JSON Schema + C# serialization classes via bonsai.sgen
    convert_pydantic_to_bonsai(
        experiment,
        model_name="TestExperiment",
        root_element="Root",
        cs_namespace="TestDataSchema",
        json_schema_output_dir=output_path,
        cs_output_dir=output_path.parent / "Extensions",
        cs_serializer=[BonsaiSgenSerializers.JSON, BonsaiSgenSerializers.YAML],
    )


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local")
    main(output_dir)
