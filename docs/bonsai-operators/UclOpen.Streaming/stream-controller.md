# Stream Controller

The `StreamController` operator owns the ZeroMQ publisher sockets and the identity carried by every streamed message. It assembles a `StreamIdentity` subject from the rig ID, subject ID and session ID, which all packing operators consume to build their topic and header. There should be a `StreamController` at the top of any workflow that streams. It must exist so that the `StreamIdentity` subject is available, and so that something binds the sockets. without it the packing operators have nowhere to publish.

---

## Bonsai workflow

:::workflow
![StreamController](~/assets/workflows/streaming/StreamController.svg){data-bonsai="~/src/UclOpen.Streaming/StreamController.bonsai"}
:::

The operator publishes the rig identity once, then opens two publisher sockets:

- **DataMessage** - bound to `@tcp://0.0.0.0:5556`, carrying everything from [Pack Data Message](pack-data-message.md).
- **VideoMessage** - bound to `@tcp://0.0.0.0:5558`, carrying everything from [Pack Video Message](pack-video-message.md).

Within each socket any number of streams share the connection, separated by topic. This can be extended to further sockets in future.

Packing operators reach the sockets through a `MulticastSubject` rather than a direct conenction, so a `StreamController` anywhere in the workflow serves every packer.

### Externalized properties

| Property | Default | Description |
|----------|---------|-------------|
| `RigId` | `MyRig` | The rig identifier included in every published topic |
| `SubjectId` | `Algernon` | The subject identifier, matching the logging session directory |
| `SessionId` | `001` | The session identifier, matching the logging session directory |

`SubjectId` and `SessionId` combine into the `sessionKey` header field. Setting them to match the values given to `LogController` is what lets a streamed record be traced back to the data on disk.

---

## Usage

One `StreamController` per workflow. `RigId` must match the `RigId` set on any [Receive Stream](receive-stream.md) or [Receive Video](receive-video.md).

The default `0.0.0.0` binds on all interfaces, which is what cross-machine streaming needs. See the [overview](streaming.md#cross-machine-setup).
