using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Reactive.Linq;
using System.Reflection;
using Bonsai;
using Bonsai.Harp;

namespace UclOpen.HardwareSimulation
{
    /// <summary>
    /// Simulates a Harp Behavior board, emitting a randomly selected register message on each tick
    /// of an internal timer. Intended for exercising logging workflows without physical hardware.
    /// </summary>
    [Combinator(MethodName = nameof(Generate))]
    [Description("Simulates a Harp Behavior board by emitting a random register message on each tick of an internal timer.")]
    [WorkflowElementCategory(ElementCategory.Source)]
    public class BehaviorDeviceSimulator
    {
        // The low nibble of a PayloadType encodes the size in bytes of a single element,
        // so Float (0x44) is four bytes and S16 (0x82) is two.
        const int PayloadSizeMask = 0x0F;

        static readonly ReadOnlyCollection<HarpRegisterInfo> registers = DiscoverRegisters();

        /// <summary>
        /// The registers of the simulated device, in address order.
        /// </summary>
        public static ReadOnlyCollection<HarpRegisterInfo> Registers
        {
            get { return registers; }
        }

        [Description("The interval between emitted messages.")]
        public TimeSpan Period { get; set; } = TimeSpan.FromMilliseconds(10);

        [Description("The seed used to select registers and payloads. Fixed by default so that runs are reproducible.")]
        public int Seed { get; set; }

        [Description("The type of the emitted messages.")]
        public MessageType MessageType { get; set; } = MessageType.Event;

        [Description("Replaces the random payload with the index of the message, so that a log can be " +
                     "checked for messages which were never recorded.")]
        public bool SequencePayload { get; set; }

        /// <summary>
        /// Generates an observable sequence of simulated Harp messages.
        /// </summary>
        public IObservable<HarpMessage> Generate()
        {
            var period = Period;
            var seed = Seed;
            var messageType = MessageType;
            var sequencePayload = SequencePayload;

            // Deferred so that each subscription gets its own generator state rather than
            // sharing a single sequence across subscriptions.
            return Observable.Defer(() =>
            {
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

        /// <summary>
        /// Builds the register table by reflecting over the Harp.Behavior device assembly, so that
        /// the simulator stays in step with the package rather than duplicating a hand written list.
        /// </summary>
        static ReadOnlyCollection<HarpRegisterInfo> DiscoverRegisters()
        {
            const BindingFlags ConstantFlags = BindingFlags.Public | BindingFlags.Static;
            var result = new List<HarpRegisterInfo>();
            foreach (var type in typeof(Harp.Behavior.Device).Assembly.GetExportedTypes())
            {
                // Every generated register class declares these three constants. The companion
                // Timestamped* classes do not, which is what keeps them out of the table.
                var address = type.GetField("Address", ConstantFlags);
                var registerType = type.GetField("RegisterType", ConstantFlags);
                var registerLength = type.GetField("RegisterLength", ConstantFlags);
                if (address == null || address.FieldType != typeof(int) ||
                    registerType == null || registerType.FieldType != typeof(PayloadType) ||
                    registerLength == null || registerLength.FieldType != typeof(int))
                {
                    continue;
                }

                result.Add(new HarpRegisterInfo(
                    type.Name,
                    (int)address.GetValue(null),
                    (PayloadType)registerType.GetValue(null),
                    (int)registerLength.GetValue(null)));
            }

            result.Sort((left, right) => left.Address.CompareTo(right.Address));
            if (result.Count == 0)
            {
                throw new InvalidOperationException(
                    "No Harp.Behavior registers were discovered. The generated register layout may have changed.");
            }

            return result.AsReadOnly();
        }
    }

    /// <summary>
    /// Describes a single register of a simulated Harp device.
    /// </summary>
    public sealed class HarpRegisterInfo
    {
        public HarpRegisterInfo(string name, int address, PayloadType payloadType, int length)
        {
            Name = name;
            Address = address;
            PayloadType = payloadType;
            Length = length;
        }

        /// <summary>
        /// The name of the register, as declared by the device package.
        /// </summary>
        public string Name { get; }

        /// <summary>
        /// The address the register is published on.
        /// </summary>
        public int Address { get; }

        /// <summary>
        /// The type of a single element of the register payload.
        /// </summary>
        public PayloadType PayloadType { get; }

        /// <summary>
        /// The number of elements in the register payload.
        /// </summary>
        public int Length { get; }

        public override string ToString()
        {
            return $"{Name} (address {Address}, {Length}x{PayloadType})";
        }
    }
}
