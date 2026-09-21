using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;

namespace UclOpen.HarpLogTool
{
    /// <summary>
    /// Command line options for the tool.
    /// </summary>
    sealed class Options
    {
        // Options which only make sense when the tool is driving a workflow itself.
        static readonly string[] RunOnlyArguments =
        {
            "--count", "--repeats", "--workflow", "--workflow-directory",
            "--log-name", "--subject-id", "--session-id", "--keep-binaries"
        };

        readonly HashSet<string> specified = new HashSet<string>(StringComparer.Ordinal);

        public IReadOnlyList<int> Counts { get; private set; } = new[] { 1, 5, 20, 100 };

        public int Repeats { get; private set; } = 1;

        public string WorkflowFileName { get; private set; } = "LogHarpTest.bonsai";

        public string WorkflowDirectory { get; private set; }

        public string LogName { get; private set; } = "SimulatedBehavior";

        public string SubjectId { get; private set; } = "TestSubject";

        public string SessionId { get; private set; } = "001";

        /// <summary>
        /// An existing folder of Harp logs to decode instead of running a workflow.
        /// </summary>
        public string InputPath { get; private set; }

        public string Pattern { get; private set; } = "*.bin";

        public string OutputPath { get; private set; } =
            Path.Combine(Path.GetTempPath(), "UclOpen.HarpLogTool");

        public bool KeepBinaries { get; private set; }

        public bool ShowHelp { get; private set; }

        /// <summary>
        /// Whether the tool should decode existing logs rather than running a workflow.
        /// </summary>
        public bool IsDecodeOnly
        {
            get { return InputPath != null; }
        }

        public static Options Parse(string[] args)
        {
            var options = new Options();
            for (var i = 0; i < args.Length; i++)
            {
                var argument = args[i];
                options.specified.Add(argument);
                switch (argument)
                {
                    case "-h":
                    case "--help":
                        options.ShowHelp = true;
                        return options;
                    case "--count":
                        options.Counts = ParseCounts(ReadValue(args, ref i, argument));
                        break;
                    case "--repeats":
                        options.Repeats = ParsePositive(ReadValue(args, ref i, argument), argument);
                        break;
                    case "--workflow":
                        options.WorkflowFileName = ReadValue(args, ref i, argument);
                        break;
                    case "--workflow-directory":
                        options.WorkflowDirectory = Path.GetFullPath(ReadValue(args, ref i, argument));
                        break;
                    case "--log-name":
                        options.LogName = ReadValue(args, ref i, argument);
                        break;
                    case "--subject-id":
                        options.SubjectId = ReadValue(args, ref i, argument);
                        break;
                    case "--session-id":
                        options.SessionId = ReadValue(args, ref i, argument);
                        break;
                    case "--input":
                        options.InputPath = Path.GetFullPath(ReadValue(args, ref i, argument));
                        break;
                    case "--pattern":
                        options.Pattern = ReadValue(args, ref i, argument);
                        break;
                    case "--output":
                        options.OutputPath = Path.GetFullPath(ReadValue(args, ref i, argument));
                        break;
                    case "--keep-binaries":
                        options.KeepBinaries = true;
                        break;
                    default:
                        throw new FormatException($"Unrecognized argument '{argument}'.");
                }
            }

            options.Validate();
            return options;
        }

        void Validate()
        {
            if (!IsDecodeOnly)
            {
                return;
            }

            var conflicting = RunOnlyArguments.Where(specified.Contains).ToArray();
            if (conflicting.Length > 0)
            {
                throw new FormatException(
                    $"'--input' decodes existing logs and does not run a workflow, so it cannot be " +
                    $"combined with {string.Join(", ", conflicting)}.");
            }
        }

        static string ReadValue(string[] args, ref int index, string argument)
        {
            if (index + 1 >= args.Length)
            {
                throw new FormatException($"'{argument}' requires a value.");
            }

            return args[++index];
        }

        static IReadOnlyList<int> ParseCounts(string value)
        {
            var counts = value
                .Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(entry => ParsePositive(entry.Trim(), "--count"))
                .ToArray();
            if (counts.Length == 0)
            {
                throw new FormatException("'--count' requires at least one value.");
            }

            return counts;
        }

        static int ParsePositive(string value, string argument)
        {
            if (!int.TryParse(value, NumberStyles.Integer, CultureInfo.InvariantCulture, out var parsed) ||
                parsed < 1)
            {
                throw new FormatException($"'{argument}' expects a positive integer but found '{value}'.");
            }

            return parsed;
        }

        public static void WriteUsage(TextWriter writer)
        {
            writer.WriteLine("Decodes Harp binary logs into CSV, either by running a logging workflow");
            writer.WriteLine("or by reading a folder of logs collected elsewhere, such as from the Bonsai editor.");
            writer.WriteLine();
            writer.WriteLine("Usage: UclOpen.HarpLogTool [options]");
            writer.WriteLine();
            writer.WriteLine("Decoding existing logs:");
            writer.WriteLine("  --input <directory>      Decode the logs already in this folder, searched");
            writer.WriteLine("                           recursively. No workflow is run.");
            writer.WriteLine("  --pattern <glob>         Which files to decode. Default *.bin.");
            writer.WriteLine();
            writer.WriteLine("Running a workflow:");
            writer.WriteLine("  --count <n[,n...]>       Count values to run, each independently. Default 1,5,20,100.");
            writer.WriteLine("  --repeats <n>            How many times to run each count. Default 1.");
            writer.WriteLine("  --workflow <file>        Workflow to run. Default LogHarpTest.bonsai.");
            writer.WriteLine("  --workflow-directory <d> Where to find the workflow and extensions.");
            writer.WriteLine("                           Defaults to the UclOpen.Logging.Tests build output.");
            writer.WriteLine("  --log-name <name>        HarpLogName property. Default SimulatedBehavior.");
            writer.WriteLine("  --subject-id <id>        SubjectId property. Default TestSubject.");
            writer.WriteLine("  --session-id <id>        SessionId property. Default 001.");
            writer.WriteLine("  --keep-binaries          Keep the raw logs instead of deleting them.");
            writer.WriteLine();
            writer.WriteLine("Common:");
            writer.WriteLine("  --output <directory>     Where to write samples.csv and summary.csv.");
            writer.WriteLine("                           Default %TEMP%\\UclOpen.HarpLogTool.");
            writer.WriteLine("  -h, --help               Show this help.");
            writer.WriteLine();
            writer.WriteLine("samples.csv holds one row per decoded message in both modes. summary.csv holds");
            writer.WriteLine("one row per run when running a workflow, and one row per file when decoding.");
            writer.WriteLine("RequestedCount and Run are left empty when decoding existing logs.");
            writer.WriteLine();
            writer.WriteLine("Exits 0 when every run recorded exactly the requested number of samples, and");
            writer.WriteLine("when decoding, whenever every file decoded cleanly.");
        }
    }
}
