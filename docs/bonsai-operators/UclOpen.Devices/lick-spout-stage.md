# Lick Spout Stage

The Lick Spout Stage is an Arduino-driven 5-axis stepper rig used to position a pair of lick spouts in front of the animal. The driver speaks a small byte protocol over a serial port to move the stage to named absolute positions defined in the rig configuration.

---

## Python schema

`LickSpoutStageDriver` is defined in `ucl_open.devices` and extends `SerialDevice`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `port_name` | `str` | - | Serial port the device is connected to (e.g. `COM3`) |
| `baud_rate` | `int` | `9600` | Baud rate for serial communication |
| `move` | `Byte` | `71` | Command byte for MOVE |
| `set_speed` | `Byte` | `72` | Command byte for SET SPEED |
| `set_acceleration` | `Byte` | `73` | Command byte for SET ACCELERATION |
| `speed` | `int` | `300` | Default motor speed (steps/s) |
| `acceleration_major` | `int` | `20` | Major acceleration component |
| `acceleration_minor` | `int` | `2` | Minor acceleration component |
| `set_position` | `SpoutRigPosition` | - | Named absolute stepper positions for the 5-axis rig |

`SpoutRigPosition.positions` is a dictionary mapping a string identifier (e.g. `home`, `both_in`, `both_out`) to a `StepperPositions` with five integer fields: `left_elevation`, `right_elevation`, `right_radial`, `left_radial`, `base_transverse` (each in motor steps, mapped to motors 1–5).

### Configuration example

In your `rig.py`:

```python
from ucl_open.devices import LickSpoutStageDriver, SpoutRigPosition, StepperPositions

class Rig(...):
    ...
    lick_spout_stage: LickSpoutStageDriver = LickSpoutStageDriver(
        port_name="COM6",
        set_position=SpoutRigPosition(
            positions={
                "home": StepperPositions(
                    left_elevation=0, right_elevation=0,
                    right_radial=0, left_radial=0,
                    base_transverse=0,
                ),
                "both_in": StepperPositions(
                    left_elevation=1000, right_elevation=1000,
                    right_radial=2000, left_radial=2000,
                    base_transverse=500,
                ),
            }
        ),
    )
```

---

## Bonsai workflow

:::workflow
![LickSpoutStage](~/assets/workflows/devices/LickSpoutStage.svg){data-bonsai="~/src/UclOpen.Devices/LickSpoutStage.bonsai"}
:::

The workflow opens the serial connection, sends the configured speed and acceleration on startup, and accepts MOVE commands on an input subject that select one of the named positions in `set_position`. Externalized properties expose `PortName` and the input subject name so the workflow can be reused across rigs.
