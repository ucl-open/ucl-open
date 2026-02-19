from typing import Optional
from pydantic import Field

from ucl_open.rigs.base import BaseSchema

class TaskParameters(BaseSchema):
    rng_seed: Optional[float] = Field(default=None, description="Seed of the random number generator for these task parameters")

class Task(BaseSchema):
    task_parameters: TaskParameters