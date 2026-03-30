from datetime import datetime

from swc.aeon.schema import BaseSchema

from ucl_open.pyrat.models import Comment, PyRatSubject


class SessionConfig(BaseSchema):
    """
    Written to JSON by the Python GUI pre-session. Bonsai reads and rewrites the full
    JSON post-session with water_delivered_ml, comment(s) list, and session_end populated.
    Python re-reads it to pre-populate the post-session confirmation dialog,
    then posts water and comment(s) to PyRAT.
    """

    subject: PyRatSubject
    session_start: datetime
    workflow: str
    water_delivered_ml: float | None = None
    comment: str | None = None
    session_end: datetime | None = None
    comments: list[Comment] = []
