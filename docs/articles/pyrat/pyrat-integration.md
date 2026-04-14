# PyRAT GUI — Session Tutorial

This guide walks through running a behavioural session end-to-end using the PyRAT GUI: launching the GUI, starting Bonsai, recording in-session events, and posting the session record to PyRAT.

---

## Prerequisites

Install the PyRAT dependencies:

```bash
uv sync --extra pyrat
```

Make sure `src/PyRAT_GUI/users.json` exists with your token filled in. It is gitignored and never committed — ask a lab member if you need a copy. You can also change this path to a central (likely a server) location, but **be careful not to upload secrets to github**

---

## 1. Launch the GUI

From the repo root:

```bash
uv run python src/PyRAT_GUI/gui_Qt_refactored.py
```

Log in with your PIN when prompted. The animal table will populate from PyRAT.

---

## 2. Configure the Launch panel

In the **Launch** tab on the right:

### Bonsai executable

Click **Browse…** next to *Bonsai.exe* and select:

```
.bonsai/Bonsai.exe
```

> **Note:** Selecting the executable manually is likely to be deprecated in a future release since the GUI and Bonsai can resolve it automatically from the environment of experimental repos.

### Workflow

Click **Browse…** next to *Workflow* and select:

```
docs/workflows/pyrat/pyrat_test.bonsai
```

This is the test workflow for verifying the integration. The path is remembered by the GUI.

---

## 3. Select a mouse and start the session

Choose a mouse from the dropdown, then click **Start Session**.

The GUI will:
- Write a session JSON file to `src/PyRAT_GUI/sessions/` containing the subject info and session start timestamp
- Launch Bonsai as a subprocess, passing the session JSON path as a workflow property (Input)
- Post a `#sessionstart` comment to the animal's PyRAT record

The button disables and the status label should read *Session running…*

---

## 4. Run the experiment in Bonsai

Once Bonsai opens, run the workflow as you would an experiment. The following keyboard shortcuts post structured events in real time:

| Key | Action |
|-----|--------|
| `Ctrl` + `Right` | Post a timestamped comment to PyRAT |
| `Ctrl` + `Up` | Record a water delivery |
| `Ctrl` + `Space` | End the experiment |

Each keypress is recorded locally in Bonsai and posted to PyRAT in batch after the session ends.

When you are done, press `Ctrl` + `Space` to log the session end, then close Bonsai.

:::workflow
![PyRAT Test Workflow](../../workflows/pyrat/pyrat_test.bonsai)
:::

---

## 5. Post-session dialog

When Bonsai closes, the GUI detects it and opens the **Post Session** dialog automatically.

The dialog shows:

- **Water in session (ml)** — total water accumulated during the session (read-only)
- **Additional water (ml)** — an option to add any water given outside the workflow (e.g. manually by syringe after the session)
- **Comment (optional)** — a free-text field for any final notes

Click **Post to PyRAT** to submit. The GUI will post:
1. A `#waterdelivery` comment with the total water amount and session end timestamp
2. The optional free-text comment, if filled in
3. Any in-session comments recorded during the workflow, with optional, independent timestamps

---

## 6. What gets written to PyRAT

After a complete session, the animal's PyRAT record will contain structured comments in this format:

```
#sessionstart: pyrat_test [2026-03-30 17:52:03 UTC]
#waterdelivery: 0.50ml [2026-03-30 18:10:45 UTC]
#sessionend: pyrat_test [2026-03-30 18:10:45 UTC]
```

These can be parsed programmatically — see the [Python API reference](#python-api-reference) section below.

---

## Python API reference

The `ucl_open.pyrat` package provides typed models and an HTTP client for scripted use.

### Installation

```bash
uv sync --extra pyrat
```

For tests:

```bash
uv sync --extra pyrat --extra dev
```

### Credentials

For scripts outside the GUI, supply credentials via environment variables:

```bash
export PYRAT_URL="https://ucl-uat.pyrat.cloud/api/v3"
export PYRAT_CLIENT_TOKEN="<client token for lab>"
export PYRAT_USER_TOKEN="<your token from users.json>"
```

### Creating a client

```python
import os
from ucl_open.pyrat import PyRatClient

client = PyRatClient(
    url=os.environ["PYRAT_URL"],
    client_token=os.environ["PYRAT_CLIENT_TOKEN"],
    user_token=os.environ["PYRAT_USER_TOKEN"],
)
```

### Fetching subjects

```python
subjects = client.fetch_subjects()

for s in subjects:
    print(s.eartag_or_id, s.labid, s.weight, s.sex)
```

To fetch fewer results:

```python
subjects = client.fetch_subjects(limit=10)
```

### Recording a weight

```python
client.update_weight("CBR1-01234", weight_g=42.2)
```

### Calculating the daily water requirement

```python
from ucl_open.pyrat import calculate_water_requirement_ml

required = calculate_water_requirement_ml(weight_g=42.2)
# 0.98 ml  (formula: 40 ml/kg/day)
```

### Recording water delivery

```python
client.post_water_delivery("CBR1-01234", amount_ml=0.42)
```

This stores `#waterdelivery: 0.42ml` in PyRAT.

### Session start and end

```python
client.post_session_start("CBR1-01234", workflow="pyrat_test")
client.post_session_end("CBR1-01234", workflow="pyrat_test")
```

### Parsing session history from comments

Parsers search for specified strings in the comments of the PyRAT record, so the writers must be kept in sync for this to work, of course. 

```python
from ucl_open.pyrat import (
    parse_water_from_comment,
    parse_session_start_from_comment,
    parse_session_end_from_comment,
)

subject = client.fetch_subjects(limit=1)[0]

for comment in subject.comments:
    water = parse_water_from_comment(comment, subject.eartag_or_id)
    start = parse_session_start_from_comment(comment, subject.eartag_or_id)
    end   = parse_session_end_from_comment(comment, subject.eartag_or_id)

    if water:
        print(f"{water.delivery_date}: {water.water_amount_ml} ml")
    if start:
        print(f"Session start: {start.workflow} at {start.session_start}")
    if end:
        print(f"Session end:   {end.workflow} at {end.session_end}")
```
---

## Bonsai types (`UclOpen.Pyrat`)

C# types matching the session schema are generated into the `UclOpen.Pyrat` Bonsai package. These let Bonsai workflows read and write the session JSON produced by the GUI.

### Building and installing locally

```bash
dotnet pack UclOpen.sln
```

The nupkg packages are written to:

```
artifacts/package/release/*.nupkg
```

Install via **Tools → Manage Packages → Settings** in Bonsai, adding `artifacts/package/release/` as a local package source.

### Regenerating after schema changes

```bash
dotnet bonsai.sgen src/ucl_open/schemas/pyrat_session.json \
    --namespace UclOpen.Pyrat \
    -o src/UclOpen.Pyrat \
    --serializer json

dotnet pack UclOpen.sln
```

---