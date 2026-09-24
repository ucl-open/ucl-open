using System;
using System.ComponentModel;
using System.Reactive.Linq;
using Bonsai;
using Bonsai.Harp;

namespace UclOpen.HardwareSimulation
{
    /// <summary>
    /// Simulates a Harp device described by a device metadata file, emitting a randomly selected
    /// register message on each tick of an internal timer. Intended for exercising workflows
    /// without physical hardware.
    /// </summary>
    [Combinator(MethodName = nameof(Generate))]
    [Description("Simulates a Harp device by emitting a random register message on each tick of an internal timer.")]
    [WorkflowElementCategory(ElementCategory.Source)]
    public class HarpDeviceSimulator
    {
        // The low nibble of a PayloadType encodes the size in bytes of a single element,
        // so Float (0x44) is four bytes and S16 (0x82) is two.
        const int PayloadSizeMask = 0x0F;

        /// <summary>
        /// Gets or sets the path to the device.yml metadata file describing the simulated device.
        /// </summary>
        [FileNameFilter("Harp Device Metadata (*.yml)|*.yml|All Files|*.*")]
        [Editor("Bonsai.Design.OpenFileNameEditor, Bonsai.Design", DesignTypes.UITypeEditor)]
        [Description("The path to the device.yml metadata file describing the simulated device.")]
        public string FileName { get; set; }

        /// <summary>
        /// Gets or sets the interval between emitted messages.
        /// </summary>
        [Description("The interval between emitted messages.")]
        public TimeSpan Period { get; set; } = TimeSpan.FromMilliseconds(10);

        /// <summary>
        /// Gets or sets the seed used to select registers and payloads.
        /// </summary>
        [Description("The seed used to select registers and payloads. Fixed by default so that runs are reproducible.")]
        public int Seed { get; set; }

        /// <summary>
        /// Gets or sets the type of the emitted messages.
        /// </summary>
        [Description("The type of the emitted messages.")]
        public MessageType MessageType { get; set; } = MessageType.Event;

        /// <summary>
        /// Gets or sets a value indicating whether to replace the random payload with the index of the message.
        /// </summary>
        [Description("Replaces the random payload with the index of the message, so that a log can be " +
                     "checked for messages which were never recorded.")]
        public bool SequencePayload { get; set; }

        /// <summary>
        /// Generates an observable sequence of simulated Harp messages.
        /// </summary>
        public IObservable<HarpMessage> Generate()
        {
            var fileName = FileName;
            var period = Period;
            var seed = Seed;
            var messageType = MessageType;
            var sequencePayload = SequencePayload;

            // Deferred so that each subscription gets its own generator state rather than
            // sharing a single sequence across subscriptions, and so that a missing or malformed
            // metadata file surfaces as an error on the sequence.
            return Observable.Defer(() =>
            {
                if (string.IsNullOrEmpty(fileName))
                {
                    throw new InvalidOperationException("A device metadata file must be specified.");
                }

                var registers = HarpDeviceMetadata.Load(fileName).Registers;
                var random = new Random(seed);
                return Observable.Interval(period).Select(index =>
                {
                    var register = registers[random.Next(registers.Count)];
                    var payload = new byte[GetPayloadSize(register)];

                    // Drawn even when it is about to be overwritten, so that enabling sequence
                    // payloads does not shift the random stream and change which registers are used.
                    random.NextBytes(payload);
                    if (sequencePayload)
                    {
                        WriteSequenceNumber(payload, index);
                    }

                    // Timestamps come from the internal timer rather than the wall clock, so that
                    // a simulated run produces the same timestamps every time.
                    var timestamp = (index + 1) * period.TotalSeconds;
                    return HarpMessage.FromPayload(
                        register.Address,
                        timestamp,
                        messageType,
                        register.PayloadType,
                        payload);
                });
            });
        }

        /// <summary>
        /// Writes the message index into the payload, least significant byte first. Registers with a
        /// single byte payload can only carry indices up to 255 before wrapping.
        /// </summary>
        static void WriteSequenceNumber(byte[] payload, long index)
        {
            for (var i = 0; i < payload.Length && i < sizeof(long); i++)
            {
                payload[i] = (byte)(index >> (i * 8));
            }
        }

        static int GetPayloadSize(HarpRegisterInfo register)
        {
            return ((int)register.PayloadType & PayloadSizeMask) * register.Length;
        }
    }
}
