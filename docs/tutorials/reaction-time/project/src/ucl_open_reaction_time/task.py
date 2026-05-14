# Import core types
from typing import Literal, List
from pydantic import Field

from swc.aeon.schema import BaseSchema

from ucl_open_reaction_time import __semver__

class Trial(BaseSchema):
    temporal_frequency: float = Field(ge=0, description="Temporal frequency of the gratings in this stimulus")
    target_delay: float = Field(ge=0, description="Target response time (seconds) delay for the subject after this stimulus is presented")


class UclOpenReactionTimeTaskParameters(BaseSchema):
    trials: List[Trial] = Field(description="The sequence of trials that will be delivered in the experiment")
    max_trial_time: float = Field(description="The maximum amount of time (seconds) allowed for a response in any trial. Exceeding this time should result in the trial aborting and moving to the next trial in the sequence")
    initial_delay_time: float = Field(description="Time (in seconds) between initiation of a new trial and onset of presentation of the trial stimulus")


class UclOpenReactionTimeTaskLogic(BaseSchema):
    version: Literal[__semver__] = __semver__
    name: Literal["UclOpenReactionTime"] = Field(default="UclOpenReactionTime", description="Name of the task logic", frozen=True)
    task_parameters: UclOpenReactionTimeTaskParameters = Field(description="Parameters of the task logic")