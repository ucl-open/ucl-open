# Arduino LED Driver

The Arduino LED Driver is a serial device used to drive one or more LEDs from digital output pins on an Arduino board. It is configured at startup with the pin assignment and sampling interval, and forwards drive commands from Bonsai to the board over the serial port.

---

## Python schema

`LedDriver` is defined in `ucl_open.devices` and extends `ArduinoDevice` (which in turn extends `SerialDevice`).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `port_name` | `str` | - | Serial port the device is connected to (e.g. `COM3`) |
| `baud_rate` | `int` | `9600` | Baud rate for serial communication |
| `sampling_interval` | `int` | - | Sampling interval, in milliseconds, between analog and I2C measurements |
| `led_controller` | `LedController` | - | LedController module specifying the digital output pin |

`LedController` has a single field, `digital_out_pin` (`int`) — the digital output pin used to drive the LED.

### Configuration example

In your `rig.py`:

```python
from ucl_open.devices import LedDriver, LedController

class Rig(...):
    ...
    led_driver: LedDriver = LedDriver(
        port_name="COM4",
        sampling_interval=10,
        led_controller=LedController(digital_out_pin=7),
    )
```

Or as YAML:

```yaml
led_driver:
  port_name: COM4
  sampling_interval: 10
  led_controller:
    digital_out_pin: 7
```

---

## Bonsai workflow

:::workflow
![ArduinoLedDriver](~/assets/workflows/devices/ArduinoLedDriver.svg){data-bonsai="~/src/UclOpen.Devices/ArduinoLedDriver.bonsai"}
:::

The workflow opens the serial connection to the Arduino, publishes incoming messages on a named `PublishSubject`, and forwards LED drive commands received on a separate input subject down to the board. Externalized properties expose `PortName`, the LED pin, and the subject names so the workflow can be reused across rigs.
