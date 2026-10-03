using Bonsai;
using System;
using System.ComponentModel;
using System.Linq;
using System.Reactive.Linq;
using Bonsai.Harp;
using System.Xml.Serialization;
using System.Xml;

namespace UclOpen.Core
{
    [Combinator]
    [Description("Groups Harp time-series in chunks of fixed size, aligned to the start of each day.")]
    [WorkflowElementCategory(ElementCategory.Combinator)]
    public class GroupByTime
    {
        public GroupByTime()
        {
            ChunkSize = 1;
        }

        // The default real-time reference is unix time in total seconds from 1904
        internal static readonly DateTime ReferenceTime = new(1904, 1, 1);

        [Description("The size of each chunk, in hours. Fractional values can be used for sub-hour chunks, e.g. 0.25 for 15 minutes.")]
        public double ChunkSize { get; set; }

        [XmlIgnore]
        [Description("The relative time at which each group will close following the end of the chunk.")]
        public TimeSpan? ClosingDuration { get; set; }

        [Browsable(false)]
        [XmlElement(nameof(ClosingDuration))]
        public string ClosingDurationXml
        {
            get
            {
                var timeShift = ClosingDuration;
                if (timeShift.HasValue) return XmlConvert.ToString(timeShift.Value);
                else return null;
            }
            set
            {
                if (!string.IsNullOrEmpty(value)) ClosingDuration = XmlConvert.ToTimeSpan(value);
                else ClosingDuration = null;
            }
        }

        DateTime GetChunkIndex(double seconds)
        {
            var currentTime = ReferenceTime.AddSeconds(seconds);
            var chunkTicks = TimeSpan.FromHours(ChunkSize).Ticks;
            if (chunkTicks <= 0)
            {
                throw new InvalidOperationException("The chunk size must be a positive number of hours.");
            }

            var timeBin = currentTime.TimeOfDay.Ticks / chunkTicks;
            return currentTime.Date.AddTicks(timeBin * chunkTicks);
        }

        public IObservable<IGroupedObservable<DateTime, Timestamped<TSource>>> Process<TSource>(IObservable<Timestamped<TSource>> source)
        {
            return source.GroupBy(value => GetChunkIndex(value.Seconds));
        }

        public IObservable<IGroupedObservable<DateTime, HarpMessage>> Process(IObservable<HarpMessage> source)
        {
            return source.GroupBy(value => GetChunkIndex(value.GetTimestamp()));
        }

        public IObservable<IGroupedObservable<DateTime, Timestamped<TSource>>> Process<TSource>(IObservable<Tuple<TSource, double>> source)
        {
            return source.GroupBy(value => GetChunkIndex(value.Item2), value => Timestamped.Create(value.Item1, value.Item2));
        }

        bool ShouldCloseChunk<TElement>(IGroupedObservable<DateTime, TElement> chunk, HarpMessage heartbeat)
        {
            var beatTimestamp = ReferenceTime.AddSeconds(heartbeat.GetTimestamp());
            var beatDelta = beatTimestamp - chunk.Key;
            return beatDelta > TimeSpan.FromHours(ChunkSize) + ClosingDuration;
        }

        public IObservable<IGroupedObservable<DateTime, Timestamped<TSource>>> Process<TSource>(
            IObservable<Timestamped<TSource>> source,
            IObservable<HarpMessage> heartbeats)
        {
            return source.GroupByUntil(
                value => GetChunkIndex(value.Seconds),
                chunk => heartbeats.FirstOrDefaultAsync(message => ShouldCloseChunk(chunk, message)));
        }

        public IObservable<IGroupedObservable<DateTime, HarpMessage>> Process(
            IObservable<HarpMessage> source,
            IObservable<HarpMessage> heartbeats)
        {
            return source.GroupByUntil(
                value => GetChunkIndex(value.GetTimestamp()),
                chunk => heartbeats.FirstOrDefaultAsync(message => ShouldCloseChunk(chunk, message)));
        }

        public IObservable<IGroupedObservable<DateTime, Timestamped<TSource>>> Process<TSource>(
            IObservable<Tuple<TSource, double>> source,
            IObservable<HarpMessage> heartbeats)
        {
            return source.GroupByUntil(
                value => GetChunkIndex(value.Item2), value => Timestamped.Create(value.Item1, value.Item2),
                chunk => heartbeats.FirstOrDefaultAsync(message => ShouldCloseChunk(chunk, message)));
        }
    }
}
