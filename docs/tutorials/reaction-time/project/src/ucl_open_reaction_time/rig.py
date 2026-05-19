from typing import Literal

from pydantic import Field
from ucl_open.core.rig import Rig
from ucl_open.devices.harp import HarpHobgoblin
from ucl_open.vision import Screen

from ucl_open_reaction_time import __semver__


class UclOpenReactionTimeRig(Rig):
    version: Literal[__semver__] = __semver__
    harp_hobgoblin: HarpHobgoblin = Field(description="Harp Hobgoblin device")
    screen: Screen = Field(description="The main display for visual stimuli")