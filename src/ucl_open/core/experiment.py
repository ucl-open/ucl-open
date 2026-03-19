from pydantic import Field
from ucl_open.core.base import BaseSchema


class Experiment(BaseSchema):
    """The base class for creating ucl-open experiment models."""

    workflow: str = Field(description="Path to the workflow running the experiment.")
    commit: str = Field(description="Commit hash of the experiment/rig repo.")
    repository_url: str = Field(
        description="The URL of the git repository used to version experiment source code."
    )
