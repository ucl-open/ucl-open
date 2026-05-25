# Log Harp Device

`LogHarpDevice` logs the raw binary message stream from a Harp device. The incoming stream is split by message type: `Read` messages are written as raw bytes to a binary `.bin` file, while `Event` messages are demultiplexed by register address into separate timestamped `.bin`files. 
The resulting `.bin` files can be loaded in Python with the `harp-python` package (`harp.read()`).

---

## Bonsai workflow

:::workflow
![LogHarpDevice](~/assets/workflows/logging/LogHarpDevice.svg){data-bonsai="~/src/UclOpen.Logging/LogHarpDevice.bonsai"}
:::

The operator has two parallel outputs:

- **LogHarp** - writes all `Read` messages as raw bytes to a single `.bin` file.
- **LogHarpDemux** - groups messages by register address and writes a separate timestamped matrix `.bin` file per register, each suffixed with the register address.

File paths are assembled from the `PathPrefix` subject (published by [LogController](log-controller.md)) and the `LogName` externalized property.

### Externalized properties

| Property | Default | Description |
|----------|---------|-------------|
| `LogName` | - | Stem added after the path prefix (e.g. `behavior`) |

---
