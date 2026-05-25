using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using System.Text;

[Combinator]
[Description("Creates a stepper motor serial command packet from a command byte and value string.")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class CreateStepperMessage
{
    public IObservable<byte[]> Process(IObservable<Tuple<byte, string>> source)
    {
        return source.Select(value =>
        {
            byte[] stringBytes = Encoding.ASCII.GetBytes(value.Item2);
            byte[] bytes = new byte[1 + stringBytes.Length];
            bytes[0] = value.Item1;
            Array.Copy(stringBytes, 0, bytes, 1, stringBytes.Length);
            return bytes;
        });
    }
}
