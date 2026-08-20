using Newtonsoft.Json;

namespace UclOpen.Streaming
{
    /// <summary>
    /// Represents the header carried in the second frame of a streamed message.
    /// </summary>
    public class StreamHeader
    {
        /// <summary>
        /// Gets or sets the identifier of the rig that published the message.
        /// </summary>
        [JsonProperty("rigId")]
        public string RigId { get; set; }

        /// <summary>
        /// Gets or sets the session key, matching the logging session directory.
        /// </summary>
        [JsonProperty("sessionKey")]
        public string SessionKey { get; set; }

        /// <summary>
        /// Gets or sets the logical stream name.
        /// </summary>
        [JsonProperty("stream")]
        public string Stream { get; set; }

        /// <summary>
        /// Gets or sets the per-stream message index. A gap indicates dropped messages.
        /// </summary>
        [JsonProperty("index")]
        public long Index { get; set; }

        /// <summary>
        /// Gets or sets how the payload frame is encoded: json, jpeg or raw.
        /// </summary>
        [JsonProperty("enc")]
        public string Encoding { get; set; }

        /// <summary>
        /// Gets or sets the name of the payload type, used to select a deserializer.
        /// </summary>
        [JsonProperty("type")]
        public string Type { get; set; }
    }

    /// <summary>
    /// Represents a received message, unpacked into its topic, header and payload.
    /// </summary>
    public class StreamMessage
    {
        /// <summary>
        /// Gets or sets the topic from the first frame.
        /// </summary>
        public string Topic { get; set; }

        /// <summary>
        /// Gets or sets the parsed header from the second frame.
        /// </summary>
        public StreamHeader Header { get; set; }

        /// <summary>
        /// Gets or sets the raw payload bytes from the third frame.
        /// </summary>
        public byte[] Payload { get; set; }

        /// <summary>
        /// Gets or sets a value indicating whether the header parsed successfully.
        /// </summary>
        public bool Valid { get; set; }

        /// <summary>
        /// Gets the payload decoded as UTF-8 text.
        /// </summary>
        public string Text
        {
            get { return Payload == null ? string.Empty : System.Text.Encoding.UTF8.GetString(Payload); }
        }
    }
}
