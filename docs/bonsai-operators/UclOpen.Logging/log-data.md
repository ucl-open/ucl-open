# Log Data

`LogData` writes a generic timestamped data stream to a CSV file. It subscribes to the `PathPrefix` subject published by [LogController](log-controller.md), appends a configurable log name and file extension, and writes each incoming value as a row. The operator is the standard building block for logging any scalar or tuple data — analog inputs, event flags, position traces — that can be expressed as comma-separated fields.

---

## Bonsai workflow

:::workflow
![LogData](~/assets/workflows/logging/LogData.svg){data-bonsai="~/src/UclOpen.Logging/LogData.bonsai"}
:::

The workflow takes a data stream as its `Source1` input, constructs the output path from `PathPrefix` + `LogName` + `Extension`, and writes rows in append mode. The `Selector` property controls which fields of the incoming type are written (defaults to `Seconds`, i.e. the Harp timestamp).

### Externalized properties

| Property | Default | Description |
|----------|---------|-------------|
| `LogName` | - | Stem added after the path prefix (e.g. `_lick_spout`) |
| `Extension` | `.csv` | File extension including the leading dot |
| `Selector` | `Seconds` | Comma-separated list of member names to write as columns |

---

## Usage

Connect any observable sequence to `LogData` to log it. Use the `Selector` to pick which fields to write:

```
# Log encoder counts with hardware timestamp
RunningWheel --> LogData
                   LogName: "_running_wheel"
                   Selector: "Seconds,Value"
```

Multiple `LogData` operators can run in parallel in the same workflow; each writes to its own file under the shared `PathPrefix`.
