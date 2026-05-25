# Behavior Board

The Behavior Board (`who_am_i = 1216`) is a Harp board commonly used as an I/O hub on UCL Open rigs. It bundles three optional modules: a pulse controller for valves and other digital outputs, a camera trigger controller, and a running-wheel encoder reader. Each of these modules can be enabled independently per rig.

---

## Python schema

`BehaviorBoard` is defined in `ucl_open.devices` and extends `HarpBehavior`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `port_name` | `str` | - | Serial port the device is connected to (e.g. `COM3`) |
| `pulse_controller` | `PulseController \| None` | `None` | Optional module for generating digital output pulses (e.g. valve opens) |
| `camera_trigger_controller` | `CameraTriggerController \| None` | `None` | Optional module for emitting camera trigger pulses |
| `running_wheel` | `RunningWheel \| None` | `None` | Optional running wheel geometry, used to convert encoder counts to speed and distance |

Sub-modules:

- `PulseController`: `active_pulses` (list of `DO1`/`DO2`/`DO3` lines enabled), `pulse_widths` (pulse width per line in microseconds).
- `CameraTriggerController`: `trigger0_frequency` and `trigger1_frequency` (Hz) for `CameraOutput0` and `CameraOutput1`.
- `RunningWheel`: `counts_per_revolution` and `wheel_diameter`.

### Configuration example

In your `rig.py`:

```python
from ucl_open.devices import (
    BehaviorBoard,
    PulseController,
    PulseWidths,
    CameraTriggerController,
    RunningWheel,
)

class Rig(...):
    ...
    behavior_board: BehaviorBoard = BehaviorBoard(
        port_name="COM5",
        pulse_controller=PulseController(
            active_pulses=["DO1", "DO2"],
            pulse_widths=PulseWidths(PulseDO1=50, PulseDO2=50, PulseDO3=0),
        ),
        camera_trigger_controller=CameraTriggerController(
            trigger0_frequency=50,
            trigger1_frequency=50,
        ),
        running_wheel=RunningWheel(counts_per_revolution=1024, wheel_diameter=0.20),
    )
```

---

## Bonsai workflow

:::workflow
![BehaviorBoard](~/assets/workflows/devices/BehaviorBoard.svg){data-bonsai="~/src/UclOpen.Devices/BehaviorBoard/BehaviorBoard.bonsai"}
:::

The top-level workflow opens the Harp serial connection, publishes the raw event stream on a named subject, and routes events into the nested sub-workflows below. Each sub-workflow exposes its own subject names so downstream nodes can subscribe to just the streams they need.

## Sub-operators

Sub-operators are nested workflows within the Behavior Board that interface with the device to configure and expose specific hardware functions. Each sub-operator subscribes to the shared event stream published by the top-level workflow and routes commands or data to its designated hardware module. They can be enabled or disabled independently via the Python schema, and each exposes its own named subjects so downstream nodes can subscribe to only the streams they need.

### PulseController

:::workflow
![PulseController](~/assets/workflows/devices/PulseController.svg){data-bonsai="~/src/UclOpen.Devices/BehaviorBoard/PulseController.bonsai"}
:::

Generates pulses on the digital output lines listed in `active_pulses`, with widths configured by `pulse_widths`. Used to drive valves and other on/off actuators in response to commands on its input subject.

### CameraTriggerController

:::workflow
![CameraTriggerController](~/assets/workflows/devices/CameraTriggerController.svg){data-bonsai="~/src/UclOpen.Devices/BehaviorBoard/CameraTriggerController.bonsai"}
:::

Emits camera trigger pulses on `CameraOutput0` and `CameraOutput1` at the configured frequencies. Pair with a triggered camera module (such as [Triggered Spinnaker](triggered-spinnaker.md)) to align video to the Harp clock.

### RunningWheel

:::workflow
![RunningWheel](~/assets/workflows/devices/RunningWheel.svg){data-bonsai="~/src/UclOpen.Devices/BehaviorBoard/RunningWheel.bonsai"}
:::

Reads the rotary encoder and converts counts into wheel speed and distance using `counts_per_revolution` and `wheel_diameter` from the rig configuration.

### Timestamps

:::workflow
![Timestamps](~/assets/workflows/devices/Timestamps.svg){data-bonsai="~/src/UclOpen.Devices/BehaviorBoard/Timestamps.bonsai"}
:::

Derives a hardware-clock timebase from the Behavior Board's event stream and publishes it on a named subject. Other modules can use `WithLatestFrom` against this subject to stamp their own data with the Harp clock, keeping all rig data on a single timebase.
