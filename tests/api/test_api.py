import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from harp.io import MessageType, to_file

from ucl_open import api
from ucl_open.api import Device, DotMap, csv_reader, harp_reader, video_reader

DEVICE_YML = """\
%YAML 1.1
---
device: TestDevice
whoAmI: 0
firmwareVersion: "0.1"
hardwareTargets: "0.1"
registers:
  AnalogData:
    address: 44
    type: S16
    length: 2
    access: Event
    payloadSpec:
      Channel0:
        offset: 0
      Channel1:
        offset: 1
  Counter:
    address: 45
    type: U32
    access: Event
"""

SESSION = "ses-001_date-2026-10-03T16-14-20"
CHUNK_SECONDS = 36


def chunk_name(seconds: float) -> str:
    return api.to_datetime(seconds).strftime("%Y-%m-%dT%H-%M-%S")


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    """Generates a session with three 36-second chunks for each device."""
    session = tmp_path / "sub-Test" / SESSION
    for chunk in range(3):
        start = chunk * CHUNK_SECONDS
        times = start + np.arange(0, CHUNK_SECONDS, 6.0)
        name = chunk_name(start)

        csv_dir = session / "MousePosition"
        csv_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"Seconds": times, "Value.X": times * 2, "Value.Y": times * 3}).to_csv(
            csv_dir / f"MousePosition_{name}.csv", index=False
        )

        video_dir = session / "Video"
        video_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"Seconds": times, "Value.Width": 640, "Value.Height": 480}).to_csv(
            video_dir / f"Video_{name}.csv", index=False
        )

        harp_dir = session / "HarpDevice"
        harp_dir.mkdir(parents=True, exist_ok=True)
        analog = pd.DataFrame({"a": np.arange(len(times)), "b": -np.arange(len(times))}, index=times)
        to_file(
            analog,
            harp_dir / f"HarpDevice_44_{name}.bin",
            address=44,
            dtype=np.dtype(np.int16),
            message_type=MessageType.EVENT,
        )
        counter = pd.DataFrame({"c": np.arange(len(times))}, index=times)
        to_file(
            counter,
            harp_dir / f"HarpDevice_45_{name}.bin",
            address=45,
            dtype=np.dtype(np.uint32),
            message_type=MessageType.EVENT,
        )

    (tmp_path / "device.yml").write_text(DEVICE_YML)
    return session


@pytest.fixture
def experiment(dataset: Path) -> DotMap:
    return DotMap(
        [
            Device("HarpDevice", harp_reader(dataset.parents[1] / "device.yml")),
            Device("MousePosition", csv_reader()),
            Device("Video", video_reader()),
        ]
    )


def test_load_csv_stitches_chunks(dataset: Path, experiment: DotMap):
    data = api.load(dataset, experiment.MousePosition)
    assert list(data.columns) == ["Value.X", "Value.Y"]
    assert len(data) == 18
    assert data.index.is_monotonic_increasing
    assert data.index[0] == api.to_datetime(0.0)
    assert data.index[-1] == api.to_datetime(102.0)


def test_load_csv_with_columns(dataset: Path):
    data = api.load(dataset, api.Csv("MousePosition_*", columns=("x", "y")))
    assert list(data.columns) == ["x", "y"]


def test_load_harp_registers(dataset: Path, experiment: DotMap):
    analog = api.load(dataset, experiment.HarpDevice.AnalogData)
    assert list(analog.columns) == ["Channel0", "Channel1"]
    assert len(analog) == 18

    counter = api.load(dataset, experiment.HarpDevice.Counter)
    assert list(counter.columns) == ["Counter"]
    assert len(counter) == 18


def test_load_video(dataset: Path, experiment: DotMap):
    data = api.load(dataset, experiment.Video)
    assert len(data) == 18
    first = data.iloc[0]
    assert first["_frame"] == 0
    assert first["_path"].endswith(f"Video_{chunk_name(0)}.avi")
    assert first["_epoch"] == SESSION


def test_load_from_parent_directory(dataset: Path, experiment: DotMap):
    data = api.load(dataset.parents[1], experiment.MousePosition)
    assert len(data) == 18


def test_load_time_range_spanning_chunk_boundary(dataset: Path, experiment: DotMap):
    start = api.to_datetime(30.0)
    end = api.to_datetime(48.0)
    data = api.load(dataset, experiment.MousePosition, start=start, end=end)
    assert list(api.to_seconds(data.index)) == [30.0, 36.0, 42.0, 48.0]


def test_load_time_range_exclusive(dataset: Path, experiment: DotMap):
    start = api.to_datetime(30.0)
    end = api.to_datetime(48.0)
    data = api.load(dataset, experiment.MousePosition, start=start, end=end, inclusive="neither")
    assert list(api.to_seconds(data.index)) == [36.0, 42.0]


def test_load_time_range_naive_datetime(dataset: Path, experiment: DotMap):
    start = datetime.datetime(1904, 1, 1, 0, 1, 12)
    data = api.load(dataset, experiment.MousePosition, start=start)
    assert len(data) == 6


def test_load_time_range_inside_multi_hour_chunk(tmp_path: Path):
    """A chunk longer than one hour must still be read when the range starts inside it."""
    session = tmp_path / SESSION / "MousePosition"
    session.mkdir(parents=True)
    times = np.array([0.0, 3600.0 * 1.5, 3600.0 * 2.5])
    pd.DataFrame({"Seconds": times[:2], "X": [0, 1]}).to_csv(
        session / f"MousePosition_{chunk_name(0)}.csv", index=False
    )
    pd.DataFrame({"Seconds": times[2:], "X": [2]}).to_csv(
        session / f"MousePosition_{chunk_name(7200)}.csv", index=False
    )
    data = api.load(tmp_path, api.Csv("MousePosition_*"), start=api.to_datetime(3600.0))
    assert list(data.X) == [1, 2]


def test_load_missing_data_is_empty(dataset: Path):
    data = api.load(dataset, api.Csv("Missing_*", columns=("x",)))
    assert data.empty
    assert list(data.columns) == ["x"]
