using Bonsai;
using System;
using System.ComponentModel;
using System.Reactive.Linq;

namespace UclOpen.Pyrat
{
    [Combinator]
    [Description("Adds the specified amount to the WaterDeliveredMl field of the session config.")]
    [WorkflowElementCategory(ElementCategory.Transform)]
    public class UpdateWaterAmount
    {
        [Description("Amount of water in mL to add to the existing WaterDeliveredMl value.")]
        public double Amount { get; set; }

        public IObservable<SessionConfig> Process(IObservable<SessionConfig> source)
        {
            return source.Select(value =>
            {
                value.WaterDeliveredMl = (value.WaterDeliveredMl ?? 0) + Amount;
                return value;
            });
        }
    }
}
