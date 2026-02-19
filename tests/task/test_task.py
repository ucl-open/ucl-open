import unittest
from pydantic import Field, ValidationError
from ucl_open.rigs.task import Task, TaskParameters

class TaskParametersImplementation(TaskParameters):
    test_parameter: int = Field(default=27, description="A test integer parameter")


class TestTaskParameters(unittest.TestCase):
    def test_custom_rng_seed(self):
        params = TaskParameters(rng_seed=31415.0)
        self.assertEqual(params.rng_seed, 31415.0)
        
    def test_serialization(self):
        params = TaskParametersImplementation(rng_seed=31415.0, test_parameter=50)
        json_str = params.model_dump_json()
        deserialized = TaskParametersImplementation.model_validate_json(json_str)
        self.assertEqual(params.rng_seed, deserialized.rng_seed)
        self.assertEqual(params.test_parameter, deserialized.test_parameter)
        
        
if __name__ == "__main__":
    unittest.main()