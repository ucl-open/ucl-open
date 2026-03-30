from __future__ import annotations

import re
from datetime import date, datetime

from pydantic import Field

from swc.aeon.schema import BaseSchema


class PyRatSubject(BaseSchema):
    """Subject record from PyRAT. Matches the complete self.info dict structure in the GUI."""

    eartag_or_id: str = Field(description="PyRAT eartag or ID.")
    labid: str | None = Field(default=None, description="Lab ID.")
    sex: str | None = Field(default=None, description="Biological sex.")
    weight: float | None = Field(default=None, description="Most recent weight in grams.")
    age_days: int | None = Field(default=None, description="Age in days.")
    age_weeks: int | None = Field(default=None, description="Age in weeks.")
    strain_name_with_id: str | None = Field(default=None, description="Strain name with ID.")
    responsible_fullname: str | None = Field(default=None, description="Responsible researcher.")
    responsible_id: str | int | None = Field(default=None, description="Responsible researcher ID.")
    mutations: list[Mutation] = Field(default_factory=list, description="Mutations.")
    cagenumber: str | None = Field(default=None, description="Cage number.")
    cagetype: str | None = Field(default=None, description="Cage type.")
    room_name: str | None = Field(default=None, description="Room name.")
    date_last_comment: str | None = Field(default=None, description="Date of last comment.")
    comments: list[Comment] = Field(default_factory=list, description="Recent comments.")

class Mutation(BaseSchema):
    """A single mutation entry as returned in a PyRAT record."""

    mutationname: str = Field(description="Name of the mutation.")
    mutationgrade: str = Field(description="Grade: wt, het, hom, etc.")


class WeightRecord(BaseSchema):
    """Input model for posting a body-weight measurement to PyRAT."""

    eartag_or_id: str = Field(description="PyRAT eartag or ID.")
    weight: float = Field(description="Body weight in grams.")
    weight_time: datetime = Field(description="UTC datetime of measurement (ISO 8601).")


class WaterDeliveryComment(BaseSchema):
    """Parsed water-delivery record from a PyRAT comment."""

    eartag_or_id: str = Field(description="PyRAT eartag or ID.")
    water_amount_ml: float = Field(description="Volume of water delivered in ml.")
    delivery_date: date | None = Field(default=None, description="Calendar date of delivery (from comment.created).")


class Comment(BaseSchema):
    """A comment entry as returned in a PyRAT record."""

    created: datetime | None = Field(default=None, description="UTC datetime of the comment.")
    content: str = Field(default="", description="Comment text.")


class SessionStartComment(BaseSchema):
    """Parsed session-start event from a PyRAT comment."""

    eartag_or_id: str = Field(description="PyRAT eartag or ID.")
    workflow: str = Field(description="Workflow name.")
    session_start: datetime | None = Field(default=None, description="UTC datetime of session start.")


class SessionEndComment(BaseSchema):
    """Parsed session-end event from a PyRAT comment."""

    eartag_or_id: str = Field(description="PyRAT eartag or ID.")
    workflow: str = Field(description="Workflow name.")
    session_end: datetime | None = Field(default=None, description="UTC datetime of session end.")


water_re = re.compile(r"^#waterdelivery: ([\d.]+)ml(?: \[.+\])?$")
session_start_re = re.compile(r"^#sessionstart: (.+?) \[(.+)\]$")
session_end_re = re.compile(r"^#sessionend: (.+?) \[(.+)\]$")
timestamp_fmt = "%Y-%m-%d %H:%M:%S UTC"


def parse_timestamp(s: str) -> datetime | None:
    """Parse a UTC timestamp string in the format '%Y-%m-%d %H:%M:%S UTC', returning None on failure."""
    try:
        return datetime.strptime(s, timestamp_fmt)
    except ValueError:
        return None


def parse_water_from_comment(comment: Comment, eartag_or_id: str) -> WaterDeliveryComment | None:
    """Return a WaterDeliveryComment if the comment matches the #waterdelivery: {amount}ml format, else None."""
    m = water_re.match(comment.content or "")
    if m is None:
        return None
    return WaterDeliveryComment(
        eartag_or_id=eartag_or_id,
        water_amount_ml=float(m.group(1)),
        delivery_date=comment.created.date() if comment.created else None,
    )


def parse_session_start_from_comment(comment: Comment, eartag_or_id: str) -> SessionStartComment | None:
    """Return a SessionStartComment if the comment matches the #sessionstart: {workflow} [{timestamp}] format, else None."""
    m = session_start_re.match(comment.content or "")
    if m is None:
        return None
    return SessionStartComment(
        eartag_or_id=eartag_or_id,
        workflow=m.group(1),
        session_start=parse_timestamp(m.group(2)),
    )


def parse_session_end_from_comment(comment: Comment, eartag_or_id: str) -> SessionEndComment | None:
    """Return a SessionEndComment if the comment matches the #sessionend: {workflow} [{timestamp}] format, else None."""
    m = session_end_re.match(comment.content or "")
    if m is None:
        return None
    return SessionEndComment(
        eartag_or_id=eartag_or_id,
        workflow=m.group(1),
        session_end=parse_timestamp(m.group(2)),
    )