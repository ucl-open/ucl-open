using Bonsai.Harp;

namespace UclOpen.HardwareSimulation
{
    /// <summary>
    /// Describes a single register of a simulated Harp device.
    /// </summary>
    public sealed class HarpRegisterInfo
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="HarpRegisterInfo"/> class.
        /// </summary>
        public HarpRegisterInfo(string name, int address, PayloadType payloadType, int length)
        {
            Name = name;
            Address = address;
            PayloadType = payloadType;
            Length = length;
        }

        /// <summary>
        /// The name of the register, as declared by the device metadata.
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

        /// <inheritdoc/>
        public override string ToString()
        {
            return $"{Name} (address {Address}, {Length}x{PayloadType})";
        }
    }
}
