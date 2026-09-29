# Receive Video

`ReceiveVideo` subscribes to a video stream on a remote machine and decodes each arriving frame back into an image. It has the reverse behaviour to [Pack Video Message](pack-video-message.md) and differs from [Receive Stream](receive-stream.md) only in what it does with the payload: JPEG frames are decoded rather than deserialized from JSON.

---

## Bonsai workflow

:::workflow
![ReceiveVideo](~/assets/workflows/streaming/ReceiveVideo.svg){data-bonsai="~/src/UclOpen.Streaming/ReceiveVideo.bonsai"}
:::

- **DecodeImage** - decodes the JPEG payload into an image.
- **SelectStreamValue** - zips the decoded image back with the message it came from and attaches
  `SessionKey` and `Index`.

### Externalized properties

| Property | Default | Description |
|----------|---------|-------------|
| `RigId` | `MyRig` | Identifier of the rig to subscribe to. Must match the publisher's `RigId` |
| `StreamName` | `video` | Video stream to subscribe to. Must match the publisher's `StreamName` |
| `ConnectionString` | `>tcp://127.0.0.1:5558` | Publisher endpoint to connect to, for example `>tcp://rig-machine:5558` |
| `Mode` | `Unchanged` | Optional conversion applied to the decoded image, for example grayscale |

Note the default port is `5558`, not the `5556` used for data — [Stream Controller](stream-controller.md)
binds video on its own socket, since video is typically far more dense than many streams of data.

---

## Usage

Connect the output to a visualizer to watch a remote camera:

```
ReceiveVideo -> Value
  RigId = MyRig
  StreamName = video
  ConnectionString = >tcp://rig-machine:5558
```

Frames arrive at the publisher's `SampleInterval` rate, resized and JPEG-compressed. The stream is
for monitoring. Video frames and a subscriber have been through a lossy round trip and should not be analysed.
