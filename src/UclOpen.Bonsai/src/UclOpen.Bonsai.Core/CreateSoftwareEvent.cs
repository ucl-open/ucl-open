using Bonsai;
using System;
using System.ComponentModel;
using System.Linq;
using System.Reactive.Linq;
using Bonsai.Harp;
using UclOpen.Core.DataTypes;

namespace UclOpen.Core
{
    [Combinator]
    [Description("Creates a fully populated SoftwareEvent a <T> generic object. If a Harp.Timestamped<T> is provided, temporal information will be added.")]
    [WorkflowElementCategory(ElementCategory.Transform)]
    public class CreateSoftwareEvent
    {
        public string EventName { get; set; } = "SoftwareEvent";

        public IObservable<SoftwareEvent> Process<TSource>(IObservable<Timestamped<TSource>> source)
        {
            var thisName = EventName;
            return source.Select(value =>
            {
                return new SoftwareEvent
                {
                    Data = value.Value,
                    Timestamp = value.Seconds,
                    TimestampSource = TimestampSource.Harp,
                    FrameIndex = null,
                    FrameTimestamp = null,
                    Name = thisName,
                };
            });
        }

        public IObservable<SoftwareEvent> Process<TSource>(IObservable<TSource> source)
        {
            var thisName = EventName;
            return source.Select(value =>
            {
                return new SoftwareEvent
                {
                    Data = value,
                    Timestamp = null,
                    TimestampSource = TimestampSource.Null,
                    FrameIndex = null,
                    FrameTimestamp = null,
                    Name = thisName,
                };
            });
        }
    }
}
