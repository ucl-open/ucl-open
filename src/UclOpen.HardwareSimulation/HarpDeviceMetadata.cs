using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using Bonsai.Harp;
using YamlDotNet.Core;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace UclOpen.HardwareSimulation
{
    /// <summary>
    /// The registers of a Harp device, as declared by its device.yml metadata file.
    /// </summary>
    /// <remarks>
    /// Only the fields needed to produce valid register messages are read. Registers marked with
    /// private visibility are left out, matching the interface the device package generates.
    /// </remarks>
    public sealed class HarpDeviceMetadata
    {
        const string PrivateVisibility = "private";

        HarpDeviceMetadata(string device, int whoAmI, ReadOnlyCollection<HarpRegisterInfo> registers)
        {
            Device = device;
            WhoAmI = whoAmI;
            Registers = registers;
        }

        /// <summary>
        /// The name of the device.
        /// </summary>
        public string Device { get; }

        /// <summary>
        /// The identifier reported by the device in its WhoAmI register.
        /// </summary>
        public int WhoAmI { get; }

        /// <summary>
        /// The public registers of the device, in address order.
        /// </summary>
        public ReadOnlyCollection<HarpRegisterInfo> Registers { get; }

        /// <summary>
        /// Reads device metadata from a device.yml file.
        /// </summary>
        public static HarpDeviceMetadata Load(string fileName)
        {
            using var reader = File.OpenText(fileName);
            try
            {
                return Parse(reader);
            }
            catch (Exception ex) when (ex is YamlException || ex is InvalidDataException)
            {
                throw new InvalidDataException($"'{fileName}' is not a valid Harp device metadata file. {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Reads device metadata from the text of a device.yml file.
        /// </summary>
        public static HarpDeviceMetadata Parse(TextReader reader)
        {
            var deserializer = new DeserializerBuilder()
                .WithNamingConvention(CamelCaseNamingConvention.Instance)
                .IgnoreUnmatchedProperties()
                .Build();

            // Device files share settings between registers with YAML merge keys (<<: *anchor),
            // which the default parser leaves unexpanded.
            var document = deserializer.Deserialize<DeviceDocument>(new MergingParser(new Parser(reader)));
            if (document?.Registers == null || document.Registers.Count == 0)
            {
                throw new InvalidDataException("The device metadata does not declare any registers.");
            }

            var registers = document.Registers
                .Where(entry => !string.Equals(entry.Value?.Visibility, PrivateVisibility, StringComparison.OrdinalIgnoreCase))
                .Select(entry => CreateRegister(entry.Key, entry.Value))
                .OrderBy(register => register.Address)
                .ToList();
            if (registers.Count == 0)
            {
                throw new InvalidDataException("The device metadata does not declare any public registers.");
            }

            return new HarpDeviceMetadata(document.Device, document.WhoAmI, registers.AsReadOnly());
        }

        static HarpRegisterInfo CreateRegister(string name, RegisterDocument register)
        {
            if (register?.Address == null)
            {
                throw new InvalidDataException($"Register '{name}' does not declare an address.");
            }

            if (!Enum.TryParse<PayloadType>(register.Type, ignoreCase: true, out var payloadType) ||
                !Enum.IsDefined(typeof(PayloadType), payloadType) ||
                (payloadType & PayloadType.Timestamp) != 0)
            {
                throw new InvalidDataException($"Register '{name}' declares an unrecognized type '{register.Type}'.");
            }

            var length = register.Length ?? 1;
            if (length < 1)
            {
                throw new InvalidDataException($"Register '{name}' declares a length of {length}.");
            }

            return new HarpRegisterInfo(name, register.Address.Value, payloadType, length);
        }

        sealed class DeviceDocument
        {
            public string Device { get; set; }

            public int WhoAmI { get; set; }

            public Dictionary<string, RegisterDocument> Registers { get; set; }
        }

        sealed class RegisterDocument
        {
            public int? Address { get; set; }

            public string Type { get; set; }

            public int? Length { get; set; }

            public string Visibility { get; set; }
        }
    }
}
