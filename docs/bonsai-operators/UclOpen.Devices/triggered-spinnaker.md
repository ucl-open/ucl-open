# Triggered Spinnaker

The Triggered Spinnaker is a Bonsai wrapper around a FLIR/Spinnaker SDK camera operating in hardware-trigger mode. Each external trigger pulse (typically from a Behavior Board camera trigger output) produces exactly one frame, so the resulting video is aligned to the rig's hardware clock rather than the PC system clock.

---

## .NET type

Unlike the other devices in this section, `TriggeredSpinnaker` is implemented as a C# Bonsai operator and is fully covered by the API reference. See [UclOpen.Video.TriggeredSpinnaker](xref:UclOpen.Video.TriggeredSpinnaker) for the property list, frame output type, and method signatures.

The `.bonsai` file in `src/UclOpen.Devices/` is a thin reusable group around the operator, exposing the camera index and stream subject names as externalized properties so the same module can drive multiple cameras on the rig.

---

## Bonsai workflow

:::workflow
![TriggeredSpinnaker](~/assets/workflows-static/devices/TriggeredSpinnaker.svg){data-bonsai="~/src/UclOpen.Devices/TriggeredSpinnaker.bonsai"}
:::

The workflow instantiates the `TriggeredSpinnaker` operator with the configured camera index, publishes the frame stream on a named subject, and forwards each frame's `VideoDataFrame` to downstream consumers (display, encoders, writers). Combine this module with a Behavior Board `CameraTriggerController` to produce a deterministic, Harp-timestamped video stream.
