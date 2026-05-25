# Harp Timestamp Generator Gen3

The Harp Timestamp Generator Gen3 (`who_am_i = 1158`) is a hardware clock synchroniser for Harp networks. It broadcasts a shared hardware timestamp over audio jack cables, allowing all devices on the rig to record data against a common timebase rather than relying on the PC system clock.

---

## Python schema

`HarpTimestampGeneratorGen3` is defined in `ucl_open.devices` with the following fields:


| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `port_name` | `str` | - | Serial port the device is connected to (e.g. `COM3`) |
| `timer_frequency` | `TimerFrequency` | `Timer1000Hz` | Rate at which timestamp events are sent to Bonsai |

`TimerFrequency` is used to set the rate at which clock events are generated on the Harp device: `Disabled`, `Timer50Hz`, `Timer100Hz`, `Timer200Hz`, `Timer500Hz`, `Timer1000Hz`. These are exposed in Bonsai by a subject that can then be used as the timestamps for the rest of your workflow. 

### Configuration example

In your `rig.py`:

```python
from ucl_open.devices import HarpTimestampGeneratorGen3, TimerFrequency

class Rig(...):
    ...
    timestamp_generator: HarpTimestampGeneratorGen3 = HarpTimestampGeneratorGen3(
        port_name="COM3",
        timer_frequency=TimerFrequency.Timer1000Hz,
    )
```

Or as YAML:

```yaml
timestamp_generator:
  port_name: COM3
  timer_frequency: Timer1000Hz
```

---

## Bonsai workflow

:::workflow
![TimestampGeneratorGen3](~/assets/workflows/devices/TimestampGeneratorGen3.svg){data-bonsai="~/src/UclOpen.Devices/TimestampGeneratorGen3.bonsai"}
:::

The workflow has three logical sections.

### 1. Initialization sequence

On startup the workflow synchronizes the PC clock to the Harp hardware clock (`SynchronizeTimestamp`), waits for that to complete (`Take(1)`), then sends a write command to configure the timer frequency after a 100 ms delay. `Concat` sequences these two messages so the timer is only configured after synchronization and we do not risk concurrent write messages clashing at the same time. Depending on how hardware is configured, timestamps before 100ms may be incorrect or at an incorrect frequency.

### 2. Device and event bus

The `Device` node opens the serial connection to the Timestamp Generator. It receives the initialization messages from the `Concat` sequence and emits all incoming Harp messages as an output stream. These are immediately published to a named `PublishSubject` (`ClockSynchronizerEvents` by default, overridable via `EventsSubjectName`). A subscription to this subject allows access to these events elsewhere in the workflow.

Three device properties are externalized so they can be set from the rig configuration: `PortName` intended to be set from configuraion yaml, and `DumpRegisters`, and `Heartbeat` set in the workflow.

### 3. Timestamps group

The `Timestamps` nested workflow subscribes to the same events subject and derives two outputs:

:::workflow
![TimestampGeneratorGen3 Timestamps](~/workflows/TimestampGeneratorGen3_Timestamps.bonsai)
:::

- **`Heartbeats` subject** - the raw once-per-second `TimestampSeconds` event stream, useful for monitoring clock health and sychronization across devices.
- **`Timebase` subject** - the running time since the workflow was started. The `Timer` register is parsed on every event; the first value is captured with `Take(1)` and held as the reference point. `WithLatestFrom` pairs each subsequent timer value with that reference, and `Subtract` computes the elapsed time since start. 

---

## Using the timebase in other modules

To stamp data from a non-Harp device with the hardware clock, subscribe to the `Timestamp` subject from the `Timestamps` group, pair it with your data stream using `WithLatestFrom`, then pass the result to `CreateTimestamped`:

> **Note:** Unlike native Harp devices, this timestamp is assigned in software when the event arrives on the PC, not in hardware at the moment of acquisition. It is therefore subject to PC scheduling jitter and USB latency. For applications requiring sub-millisecond timing accuracy, use a Harp device directly.

:::workflow
![UsingTimebase](~/workflows/UsingTimebase.bonsai)
:::
