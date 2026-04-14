using Bonsai;
using System;
using System.ComponentModel;
using System.Reactive.Linq;

namespace UclOpen.Pyrat
{
    [Combinator]
    [Description("Sets SessionEnd to the current UTC time on the session config.")]
    [WorkflowElementCategory(ElementCategory.Transform)]
    public class SetSessionEnd
    {
        public IObservable<SessionConfig> Process(IObservable<SessionConfig> source)
        {
            return source.Select(value =>
            {
                value.SessionEnd = DateTimeOffset.UtcNow;
                return value;
            });
        }
    }
}
