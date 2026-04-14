# Harp Behavior Board Interface

This module configures an existing [Harp Behavior](https://github.com/harp-tech/device.behavior) device's digital output pulses. These pulses can be used to actuate many different peripheral devices, e.g. air puff or reward drop solenoid valves, or for alignment pulses. This module can be added to a workflow that already contains a [`BehaviorBoard.bonsai`](./BehaviorBoard.bonsai) module.

## Bonsai Workflow

<img src="./assets/PulseController.svg" alt="workflow" width="500">

## Properties

This workflow exposes properties that allow a user to configure the device behavior and integrate it into larger Bonsai pipelines via `Subjects`.

### Input and Output `Subjects`

| **Property Name**         | **Input/Output** | **Description**                                                                 |
|---------------------------|------------------|---------------------------------------------------------------------------------|
| `BehaviorCommandsSubjectName`     | Input            | The name of the input subject that sends configuration and control commands. **N.B. Must match the `BehaviorCommandsSubjectName` in the properties of the `BehaviorBoard` module.**   |
| `BehaviorEventsSubjectName`       | Output           | The name of the subject that receives event messages from the device. **N.B. Must match the `BehaviorEventsSubjectName` in the properties of the `BehaviorBoard` module.**           |
| `TriggerPulseSubjectName` | Input            | Subject that carries integer values (0–2) to trigger individual output pulses on DOs |

### Configuration Parameters

| **Property Name**         | **Input/Output** | **Description**                                                                 |
|---------------------------|------------------|---------------------------------------------------------------------------------|
| `OutputPulseEnable`       | Input            | Configures which digital outputs (e.g., DO0–DO2) are enabled for pulse control. |
| `PulseDO0`                | Input            | Pulse width value (in ms) for DO0.                                              |
| `PulseDO1`                | Input            | Pulse width value (in ms) for DO1.                                              |
| `PulseDO2`                | Input            | Pulse width value (in ms) for DO2.                                              |

## Dependencies

### Bonsai:

- [Harp.Behavior](https://www.nuget.org/packages/Harp.Behavior)
- [BehaviorBoard.bonsai](BehaviorBoard.bonsai) should be placed in your workflow