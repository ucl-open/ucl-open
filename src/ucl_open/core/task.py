from typing import Optional
from pydantic import Field

from swc.aeon.schema import BaseSchema


class TaskParameters(BaseSchema):
    rng_seed: Optional[float] = Field(
        default=None, description="Seed of the random number generator for these task parameters"
    )


class Task(BaseSchema):
    task_parameters: TaskParameters
