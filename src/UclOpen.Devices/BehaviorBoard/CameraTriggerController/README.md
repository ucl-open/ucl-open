# Harp Behavior Board Interface

This module configures the PWM on DO0 and DO1 on an existing [Harp Behavior](https://github.com/harp-tech/device.behavior) board to be used as external triggers for acquiring camera frames. This module can be added to a workflow that already contains a [`BehaviorBoard.bonsai`](./BehaviorBoard.bonsai) module.

## Bonsai Workflow

<img src="./assets/CameraTriggerController.svg" alt="workflow" width="500">

## Properties

This workflow exposes properties that allow a user to connect the module to the existing behavior board and integrate it into larger Bonsai pipelines via `Subjects`. The direct output of this workflow carries the commands sent to the behavior board related to camera triggers. Trigger Frequency is also stored in a shared Subject, for ease of access elsewhere.

### Input and Output `Subjects`

| **Property Name**         | **Input/Output** | **Description**                                                                 |
|---------------------------|------------------|---------------------------------------------------------------------------------|
| `BehaviorCommandsSubjectName`     | Input            | The name of the input subject that sends configuration and control commands. **N.B. Must match the `BehaviorCommandsSubjectName` in the properties of the `BehaviorBoard` module.**   |
| `BehaviorEventsSubjectName`       | Input           | The name of the subject that receives event messages from the device. **N.B. Must match the `BehaviorEventsSubjectName` in the properties of the `BehaviorBoard` module.**           |
| `Camera0TriggerEventsSubjectName` | Output            | The name of the output subject to which camera trigger events for Trigger0 are published   |
| `Camera1TriggerEventsSubjectName` | Output            | The name of the output subject to which camera trigger events for Trigger1 are published   |

### Configuration Parameters

| **Property Name**         | **Input/Output** | **Description**                                                                 |
|---------------------------|------------------|---------------------------------------------------------------------------------|
| `Trigger0Frequency` | Input            | The frequency, in Hz, at which to trigger camera frame acquisitions on Trigger0   |
| `Trigger1Frequency` | Input            | The frequency, in Hz, at which to trigger camera frame acquisitions on Trigger1   |

## Dependencies

### Bonsai:

- [Harp.Behavior](https://www.nuget.org/packages/Harp.Behavior)
- [BehaviorBoard.bonsai](BehaviorBoard.bonsai) should be placed in your workflow