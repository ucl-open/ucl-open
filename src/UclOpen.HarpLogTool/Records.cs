using System.Collections.Generic;
using System.Globalization;
using UclOpen.Tests;

namespace UclOpen.HarpLogTool
{
    /// <summary>
    /// One decoded message, tagged with the run that produced it. RequestedCount and Run are only
    /// meaningful when the tool ran the workflow itself, and are left empty when decoding
    /// logs collected elsewhere.
    /// </summary>
    sealed class SampleRecord
    {
        public SampleRecord(int? requestedCount, int? run, string logFile, HarpLogMessage message)
        {
            RequestedCount = requestedCount;
            Run = run;
            LogFile = logFile;
            Message = message;
        }

        public int? RequestedCount { get; }

        public int? Run { get; }

        /// <summary>
        /// Path of the log file, relative to the run or input folder.
        /// </summary>
        public string LogFile { get; }

        public HarpLogMessage Message { get; }

        public static IEnumerable<string> Header
        {
            get
            {
                return new[]
                {
                    "RequestedCount", "Run", "LogFile", "FrameIndex", "Address", "Port",
                    "MessageType", "PayloadType", "IsTimestamped", "Timestamp", "PayloadHex",
                    "PayloadValue", "FrameBytes", "ChecksumValid"
                };
            }
        }

        public IEnumerable<string> ToFields()
        {
            return new[]
            {
                Format(RequestedCount),
                Format(Run),
                LogFile,
                Message.FrameIndex.ToString(CultureInfo.InvariantCulture),
                Message.Address.ToString(CultureInfo.InvariantCulture),
                Message.Port.ToString(CultureInfo.InvariantCulture),
                Message.MessageType.ToString(),
                Message.PayloadType.ToString(),
                Message.IsTimestamped.ToString(),
                Message.Timestamp?.ToString("R", CultureInfo.InvariantCulture) ?? string.Empty,
                Message.GetPayloadHex(),
                Message.GetPayloadValue().ToString(CultureInfo.InvariantCulture),
                Message.FrameLength.ToString(CultureInfo.InvariantCulture),
                Message.ChecksumValid.ToString()
            };
        }

        static string Format(int? value)
        {
            return value?.ToString(CultureInfo.InvariantCulture) ?? string.Empty;
        }
    }

    /// <summary>
    /// The outcome of a single workflow run, comparing what was asked for against what was recorded.
    /// </summary>
    sealed class RunSummary
    {
        public RunSummary(int requestedCount, int run, int logFiles, int recordedSamples)
        {
            RequestedCount = requestedCount;
            Run = run;
            LogFiles = logFiles;
            RecordedSamples = recordedSamples;
        }

        public int RequestedCount { get; }

        public int Run { get; }

        /// <summary>
        /// How many log files the run produced. This is not expected to equal the requested count,
        /// because a register that is selected more than once is logged to a single file.
        /// </summary>
        public int LogFiles { get; }

        public int RecordedSamples { get; }

        public int Missing
        {
            get { return RequestedCount - RecordedSamples; }
        }

        public bool Exact
        {
            get { return RecordedSamples == RequestedCount; }
        }

        public static IEnumerable<string> Header
        {
            get
            {
                return new[]
                {
                    "RequestedCount", "Run", "LogFiles", "RecordedSamples", "Missing", "Exact"
                };
            }
        }

        public IEnumerable<string> ToFields()
        {
            return new[]
            {
                RequestedCount.ToString(CultureInfo.InvariantCulture),
                Run.ToString(CultureInfo.InvariantCulture),
                LogFiles.ToString(CultureInfo.InvariantCulture),
                RecordedSamples.ToString(CultureInfo.InvariantCulture),
                Missing.ToString(CultureInfo.InvariantCulture),
                Exact.ToString()
            };
        }
    }

    /// <summary>
    /// What a single log file contained, used when decoding logs collected elsewhere and there is
    /// no requested sample count to compare against.
    /// </summary>
    sealed class FileSummary
    {
        public FileSummary(
            string logFile,
            int messages,
            int distinctAddresses,
            int invalidChecksums,
            double? firstTimestamp,
            double? lastTimestamp,
            string error)
        {
            LogFile = logFile;
            Messages = messages;
            DistinctAddresses = distinctAddresses;
            InvalidChecksums = invalidChecksums;
            FirstTimestamp = firstTimestamp;
            LastTimestamp = lastTimestamp;
            Error = error;
        }

        public string LogFile { get; }

        public int Messages { get; }

        public int DistinctAddresses { get; }

        public int InvalidChecksums { get; }

        public double? FirstTimestamp { get; }

        public double? LastTimestamp { get; }

        /// <summary>
        /// Why the file could not be decoded in full, or empty when it decoded cleanly.
        /// </summary>
        public string Error { get; }

        public static IEnumerable<string> Header
        {
            get
            {
                return new[]
                {
                    "LogFile", "Messages", "DistinctAddresses", "InvalidChecksums",
                    "FirstTimestamp", "LastTimestamp", "Error"
                };
            }
        }

        public IEnumerable<string> ToFields()
        {
            return new[]
            {
                LogFile,
                Messages.ToString(CultureInfo.InvariantCulture),
                DistinctAddresses.ToString(CultureInfo.InvariantCulture),
                InvalidChecksums.ToString(CultureInfo.InvariantCulture),
                FirstTimestamp?.ToString("R", CultureInfo.InvariantCulture) ?? string.Empty,
                LastTimestamp?.ToString("R", CultureInfo.InvariantCulture) ?? string.Empty,
                Error ?? string.Empty
            };
        }
    }
}
