using System;
using System.ComponentModel;
using System.Reactive.Linq;
using Bonsai;
using Newtonsoft.Json;

namespace UclOpen.Streaming
{
    /// <summary>
    /// Represents a payload serialized to JSON, together with the name of the type it came from.
    /// </summary>
    public class SerializedPayload
    {
        /// <summary>
        /// Gets or sets the name of the type the payload was serialized from.
        /// </summary>
        public string Type { get; set; }

        /// <summary>
        /// Gets or sets the payload serialized as JSON.
        /// </summary>
        public string Json { get; set; }
    }

    /// <summary>
    /// Represents an operator that serializes any value to JSON for streaming and tags it with
    /// its runtime type name.
    /// </summary>
    [Combinator]
    [Description("Serializes any value to JSON for streaming and tags it with its runtime type name.")]
    [WorkflowElementCategory(ElementCategory.Transform)]
    public class SerializeStream
    {
        /// <summary>
        /// Gets or sets the formatting applied to the serialized output.
        /// </summary>
        [Description("The formatting applied to the serialized output.")]
        public Formatting Formatting { get; set; }

        /// <summary>
        /// Serializes each value in an observable sequence to JSON.
        /// </summary>
        /// <typeparam name="TSource">The type of the elements to serialize.</typeparam>
        /// <param name="source">The sequence of values to serialize.</param>
        /// <returns>A sequence of serialized payloads.</returns>
        public IObservable<SerializedPayload> Process<TSource>(IObservable<TSource> source)
        {
            var formatting = Formatting;
            return source.Select(value => new SerializedPayload
            {
                Type = value == null ? typeof(TSource).Name : value.GetType().Name,
                Json = JsonConvert.SerializeObject(value, formatting)
            });
        }
    }
}
