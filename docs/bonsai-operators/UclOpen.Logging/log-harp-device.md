# Log Harp Device

`LogHarpDevice` logs the raw binary message stream from a Harp device. It filters for `Read` message types, writes the full message bytes to a binary `.bin` file, and optionally demultiplexes the stream by register address — writing a separate timestamped file per register. This preserves the full Harp protocol fidelity and allows the data to be decoded offline with any Harp-compatible reader.

---

## Bonsai workflow

:::workflow
![LogHarpDevice](~/assets/workflows/logging/LogHarpDevice.svg){data-bonsai="~/src/UclOpen.Logging/LogHarpDevice.bonsai"}
:::

The operator has two parallel outputs:

- **LogHarp** - writes all `Read` messages as raw bytes to a single `.bin` file.
- **LogHarpDemux** - groups messages by register address and writes a separate column-major matrix file per register, each suffixed with the register address and a timestamp column.

File paths are assembled from the `PathPrefix` subject (published by [LogController](log-controller.md)) and the `LogName` externalized property.

### Externalized properties

| Property | Default | Description |
|----------|---------|-------------|
| `LogName` | - | Stem added after the path prefix (e.g. `_behavior`) |

---

## Usage

Connect the events subject of any Harp device to `LogHarpDevice`:

```
BehaviorBoard
  BehaviorEvents --> LogHarpDevice
                       LogName: "_behavior"
```

The resulting `.bin` file can be loaded in Python with `harp.read()` or in MATLAB using the Harp toolbox. The demultiplexed files are useful for quick inspection of individual registers.
