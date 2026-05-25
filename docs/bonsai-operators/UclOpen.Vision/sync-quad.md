# Sync Quad

`SyncQuad` renders a small synchronization rectangle in the corner of a monitor at a configurable position and size. Its colour is toggled on every camera trigger by subscribing to the `SyncQuadTrigger` subject — producing an alternating bright/dark patch that is visible to a photodiode or in the camera frame itself. This gives a hardware-verifiable sync signal that ties each video frame to the Harp clock without any additional wiring.

---

## Bonsai workflow

:::workflow
![SyncQuad](~/assets/workflows/vision/SyncQuad/SyncQuad.svg){data-bonsai="~/src/UclOpen.Vision/SyncQuad/SyncQuad.bonsai"}
:::

The workflow subscribes to two subjects:

- **SyncQuadTrigger** - a pulse-per-frame signal (typically driven by the camera trigger line) that flips the quad colour on each rising edge.
- **SyncQuadState** - the current colour/brightness state, published after each flip so downstream nodes can track the sync signal in software.

The quad is rendered via BonVision's `OrthographicView` at a layer above other scene content. Its screen position (`LocationX`, `LocationY`) and extent (`ExtentX`, `ExtentY`) are read from the `RigSchema` subject at startup.

### Rig schema properties

| Property | Description |
|----------|-------------|
| `LocationX` | Horizontal centre of the quad in normalised screen coordinates |
| `LocationY` | Vertical centre of the quad in normalised screen coordinates |
| `ExtentX` | Width of the quad in normalised screen coordinates |
| `ExtentY` | Height of the quad in normalised screen coordinates |

---

## Usage

Include `SyncQuad` in any BonVision rendering workflow where frame-accurate synchronisation is required. Wire the camera trigger output from [CameraTriggerController](../UclOpen.Devices/behavior-board.md#cameratriggercontroller) to `SyncQuadTrigger`:

```
CameraTriggerController
  Camera0TriggerEvents --> SyncQuadTrigger
```

A photodiode pointed at the quad corner records the sync pulses. Because the quad state flips on every trigger, the resulting binary sequence can be correlated with the camera frame timestamps to verify that no frames were dropped.
