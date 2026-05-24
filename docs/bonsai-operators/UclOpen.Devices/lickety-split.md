# LicketySplit

The LicketySplit (`who_am_i = 1400`) is a Harp lick detector. It samples one or more capacitive/ADC channels and emits trigger events when the signal crosses configurable thresholds, providing low-latency lick timestamps on the Harp clock.

---

## Python schema

`LicketySplit` is defined in `ucl_open.devices` and extends `HarpDevice`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `port_name` | `str` | - | Serial port the device is connected to (e.g. `COM3`) |
| `channel0_trigger_threshold` | `UShort` | `0` | ADC threshold above which Channel 0 triggers a lick |
| `channel0_untrigger_threshold` | `UShort` | `0` | ADC threshold below which Channel 0 untriggers a lick |

### Configuration example

In your `rig.py`:

```python
from ucl_open.devices import LicketySplit

class Rig(...):
    ...
    lick_detector: LicketySplit = LicketySplit(
        port_name="COM7",
        channel0_trigger_threshold=1200,
        channel0_untrigger_threshold=900,
    )
```

Or as YAML:

```yaml
lick_detector:
  port_name: COM7
  channel0_trigger_threshold: 1200
  channel0_untrigger_threshold: 900
```

---

## Bonsai workflow

:::workflow
![LicketySplit](~/assets/workflows/devices/LicketySplit.svg){data-bonsai="~/src/UclOpen.Devices/LicketySplit.bonsai"}
:::

The workflow opens the Harp serial connection, writes the configured thresholds at startup, and publishes the device event stream on a named `PublishSubject`. Downstream nodes can subscribe to that subject to extract the lick trigger events stamped against the Harp hardware clock.
