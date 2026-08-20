using System;
using System.ComponentModel;
using System.Reactive.Linq;
using Bonsai;
using NetMQ;
using Newtonsoft.Json;

namespace UclOpen.Streaming
{
    /// <summary>
    /// Represents an operator that unpacks a received multipart message into its topic, header
    /// and payload. Messages with an unreadable header are marked invalid and passed through
    /// rather than terminating the sequence.
    /// </summary>
    [Combinator]
    [Description("Unpacks a received multipart message into its topic, header and payload.")]
    [WorkflowElementCategory(ElementCategory.Transform)]
    public class ParseStreamMessage
    {
        /// <summary>
        /// Unpacks each multipart message in an observable sequence.
        /// </summary>
        /// <param name="source">The sequence of received multipart messages.</param>
        /// <returns>A sequence of unpacked messages.</returns>
        public IObservable<StreamMessage> Process(IObservable<NetMQMessage> source)
        {
            return source.Select(message =>
            {
                var result = new StreamMessage { Header = new StreamHeader(), Payload = new byte[0] };
                if (message.FrameCount > 0)
                {
                    result.Topic = message[0].ConvertToString();
                }

                if (message.FrameCount > 2)
                {
                    result.Payload = message[2].ToByteArray();
                }

                if (message.FrameCount > 1)
                {
                    try
                    {
                        var header = JsonConvert.DeserializeObject<StreamHeader>(message[1].ConvertToString());
                        if (header != null)
                        {
                            result.Header = header;
                            result.Valid = true;
                        }
                    }
                    catch (JsonException)
                    {
                        result.Valid = false;
                    }
                }

                return result;
            });
        }
    }
}
