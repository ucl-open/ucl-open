from pydantic import Field
from swc.aeon.schema import Experiment


class ExperimentSession(Experiment):
    """The base class for creating ucl-open experiment models."""

    subject_id: str = Field(description="The subject id for this session.")
    session_id: str = Field(description="The session identifier.")
