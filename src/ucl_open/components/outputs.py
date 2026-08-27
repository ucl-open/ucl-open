from typing import Annotated, Literal, Union

from pydantic import Field, RootModel
from swc.aeon.schema import BaseSchema

from ucl_open.core.base import DiscriminatorTypeMixin


class BehaviorBoardOutput(DiscriminatorTypeMixin, BaseSchema):
    """An output channel on a Harp behavior board."""

    device: str = Field(
        examples=["behavior_board"], description="The name of the rig device providing this output."
    )
    port: Literal["DO0", "DO1", "DO2", "DO3", "SupplyPort0", "SupplyPort1", "SupplyPort2"] = Field(
        description="The behavior board output port."
    )


class OutputExpanderOutput(DiscriminatorTypeMixin, BaseSchema):
    """An output channel on a Harp output expander."""

    device: str = Field(
        examples=["output_expander"], description="The name of the rig device providing this output."
    )
    channel: Literal["Out0", "Out1", "Out2", "Out3", "Out4", "Out5", "Out6", "Out7", "Out8", "Out9"] = (
        Field(description="The output expander channel.")
    )


class DigitalOutput(
    RootModel[
        Annotated[Union[BehaviorBoardOutput, OutputExpanderOutput], Field(discriminator="discriminator_type")]
    ]
):
    """Discriminated digital output address (behavior board or output expander)."""

    pass
