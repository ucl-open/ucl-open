from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from ucl_open.pyrat.models import PyRatSubject, WeightRecord

ANIMAL_FIELDS: list[str] = [
    "eartag_or_id",
    "labid",
    "room_name",
    "age_days",
    "age_weeks",
    "strain_name_with_id",
    "responsible_fullname",
    "responsible_id",
    "mutations",
    "weight",
    "comments",
    "date_last_comment",
    "cagenumber",
    "cagetype",
    "sex",
]


class PyRatError(Exception):
    """Base exception for PyRat API errors."""


class PyRatAuthError(PyRatError):
    """Raised on 401 or 403 responses."""


class PyRatNotFoundError(PyRatError):
    """Raised on 404 responses."""


class PyRatAPIError(PyRatError):
    """Raised on other 4xx/5xx responses."""


class PyRatTimeoutError(PyRatError):
    """Raised when a request times out."""


class PyRatConnectionError(PyRatError):
    """Raised when a connection cannot be established."""


class PyRatClient:
    """Standalone HTTP client for the PyRAT REST API. No Qt dependency."""

    def __init__(
        self,
        url: str,
        client_token: str,
        user_token: str,
        timeout: float = 20.0,
    ) -> None:
        self._client = httpx.Client(
            base_url=url,
            auth=(client_token, user_token),
            timeout=timeout,
        )

    # Helpers ------------------------------------------------

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            raise PyRatTimeoutError(str(exc)) from exc
        except httpx.ConnectError as exc:
            raise PyRatConnectionError(str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = exc.response.text
            if status in (401, 403):
                raise PyRatAuthError(f"HTTP {status}: {body}") from exc
            if status == 404:
                raise PyRatNotFoundError(f"HTTP {status}: {body}") from exc
            raise PyRatAPIError(f"HTTP {status}: {body}") from exc

    # API ------------------------------------------------

    def verify_credentials(self) -> dict[str, Any]:
        """Return the raw credentials response (client_valid, user_valid)."""
        return self._request("GET", "credentials").json()

    def fetch_subjects(self, limit: int = 2000) -> list[PyRatSubject]:
        """Fetch the full subject list from PyRAT."""
        params: dict[str, Any] = {"k": ANIMAL_FIELDS, "l": limit}
        data: list[dict[str, Any]] = self._request("GET", "animals", params=params).json()
        return [PyRatSubject.model_validate(item) for item in data]

    def get_subject_weights(self, eartag_or_id: str) -> list[WeightRecord]:
        """Fetch weight history for a single subject."""
        data: list[dict[str, Any]] = self._request("GET", f"animals/{eartag_or_id}/weights").json()
        # API response does not include eartag_or_id in each record so inject it here to keep track.
        return [WeightRecord.model_validate({"eartag_or_id": eartag_or_id, **item}) for item in data]

    def update_weight(
        self,
        eartag_or_id: str,
        weight_g: float,
        weight_time: datetime | None = None,
    ) -> None:
        """Posts a weight measurement for a subject."""
        if weight_time is None:
            weight_time = datetime.now(timezone.utc)
        self._request(
            "POST",
            f"animals/{eartag_or_id}/weights",
            json={"weight": weight_g, "weight_time": weight_time.isoformat()},
        )

    def post_comment(self, eartag_or_id: str, comment_text: str) -> None:
        """Posts a timestamped comment to a subject record."""
        self._request(
            "POST",
            f"animals/{eartag_or_id}/comments",
            json={"comment": f"#{comment_text}"},
        )

    def post_water_delivery(self, eartag_or_id: str, amount_ml: float) -> None:
        """Posts a water delivery in the parseable #waterdelivery: {amount_ml}ml format."""
        self.post_comment(eartag_or_id, f"waterdelivery: {amount_ml}ml")

    def post_session_start(self, eartag_or_id: str, workflow: str, when: datetime | None = None) -> None:
        """Posts a session-start event in the parseable #sessionstart: {workflow} [{timestamp}] format."""
        if when is None:
            when = datetime.now(timezone.utc)
        self.post_comment(eartag_or_id, f"sessionstart: {workflow} [{when.strftime('%Y-%m-%d %H:%M:%S UTC')}]")

    def post_session_end(self, eartag_or_id: str, workflow: str, when: datetime | None = None) -> None:
        """Posts a session-end event in the parseable #sessionend: {workflow} [{timestamp}] format."""
        if when is None:
            when = datetime.now(timezone.utc)
        self.post_comment(eartag_or_id, f"sessionend: {workflow} [{when.strftime('%Y-%m-%d %H:%M:%S UTC')}]")

    # Handlers ------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PyRatClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
