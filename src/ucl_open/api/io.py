"""API for loading ucl-open data from disk."""

import datetime
import warnings
from os import PathLike
from pathlib import Path
from typing import Literal

import pandas as pd
from swc.aeon.io.api import Reader, chunk_key, to_datetime


def _set_index(data: pd.DataFrame) -> None:
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = to_datetime(data.index)
    else:
        data.index = pd.to_datetime(data.index, utc=True)
    data.index.name = "time"


def _empty(columns) -> pd.DataFrame:
    return pd.DataFrame(columns=columns, index=pd.DatetimeIndex([], name="time", tz=datetime.UTC))


def _select_chunks(
    files: list[tuple[pd.Timestamp, Path]],
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> list[Path]:
    """Selects the chunk files which may contain data in the specified time range.

    Chunk sizes are not fixed by the logging spec, so a chunk is assumed to extend
    until the start of the next chunk on file.
    """
    selected = []
    for i, (chunk, path) in enumerate(files):
        if end is not None and chunk > end:
            break
        next_chunk = files[i + 1][0] if i + 1 < len(files) else None
        if start is not None and next_chunk is not None and next_chunk <= start:
            continue
        selected.append(path)
    return selected


def load(
    root: str | PathLike | list[str] | list[PathLike],
    reader: Reader,
    start: datetime.datetime | None = None,
    end: datetime.datetime | None = None,
    inclusive: Literal["both", "neither", "left", "right"] = "both",
    epoch: str | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Extracts chunk data from the root path of a ucl-open dataset.

    Reads all chunk data using the specified data stream reader, stitching chunks
    together into a single data frame. A subset of the data can be loaded by
    specifying an optional time range. Returned data will be sorted chronologically.

    Note:
        Any timezone-naive values in `start` and `end` will be treated as UTC.

    Args:
        root: The root path, or prioritised sequence of paths, where data is stored.
            This can be a single session directory, or any parent directory of sessions.
        reader: A data stream reader object used to read chunk data from the dataset.
        start: The left bound of the time range to extract.
        end: The right bound of the time range to extract.
        inclusive: Specifies whether the `start` and `end` bounds are inclusive or exclusive.
            Options are "both", "left", "right", or "neither".
        epoch: A wildcard pattern to use when searching session directories.
        **kwargs: Optional keyword arguments to forward to `reader` when reading chunk data.

    Returns:
        A DataFrame containing extracted chunk data, indexed by time.
    """
    if isinstance(root, str | PathLike):
        root = [root]
    if start is not None:
        start = pd.to_datetime(start, utc=True)
    if end is not None:
        end = pd.to_datetime(end, utc=True)

    epoch_pattern = "**" if epoch is None else epoch
    fileset = {
        chunk_key(fname): fname
        for path in root
        for fname in Path(path).glob(f"{epoch_pattern}/**/{reader.pattern}.{reader.extension}")
    }
    files = sorted((chunk, fname) for (_, chunk), fname in fileset.items())
    files = _select_chunks(files, start, end)
    if len(files) == 0:
        return _empty(reader.columns)

    data = pd.concat([reader.read(file, **kwargs) for file in files])
    _set_index(data)
    if not data.index.is_monotonic_increasing:
        warnings.warn(f"data index for {reader.pattern} contains out-of-order timestamps!", stacklevel=2)
        data = data.sort_index(kind="stable")

    if start is not None or end is not None:
        mask = pd.Series(True, index=data.index)
        if start is not None:
            mask &= data.index >= start if inclusive in ("both", "left") else data.index > start
        if end is not None:
            mask &= data.index <= end if inclusive in ("both", "right") else data.index < end
        data = data[mask.values]
    return data
