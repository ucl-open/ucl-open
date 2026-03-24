import pytest
from pydantic import Field
from ucl_open.core.task import TaskParameters


class TaskParametersImplementation(TaskParameters):
    test_parameter: int = Field(default=27, description="A test integer parameter")


@pytest.mark.parametrize(("klass", "parameter", "expected"), [(TaskParametersImplementation, 27, 27)])
def test_serialization(klass: type[TaskParametersImplementation], parameter: int, expected: int):
    inst = klass(test_parameter=parameter)
    json_str = inst.model_dump_json()
    deserialized = klass.model_validate_json(json_str)
    assert deserialized.test_parameter == expected
