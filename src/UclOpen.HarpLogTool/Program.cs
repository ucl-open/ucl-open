using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UclOpen.Tests;

namespace UclOpen.HarpLogTool
{
    /// <summary>
    /// Decodes Harp binary logs into CSV, either by running a logging workflow for one or more
    /// values of its Count property, or by reading a folder of logs collected elsewhere.
    /// </summary>
    static class Program
    {
        static int Main(string[] args)
        {
            Options options;
            try
            {
                options = Options.Parse(args);
            }
            catch (FormatException ex)
            {
                Console.Error.WriteLine(ex.Message);
                Console.Error.WriteLine();
                Options.WriteUsage(Console.Error);
                return 2;
            }

            if (options.ShowHelp)
            {
                Options.WriteUsage(Console.Out);
                return 0;
            }

            try
            {
                Directory.CreateDirectory(options.OutputPath);
                return options.IsDecodeOnly ? Decode(options) : RunSweep(options);
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex.Message);
                return 1;
            }
        }

        // ------------------------------------------------------------------ Decoding existing logs
        static int Decode(Options options)
        {
            if (!Directory.Exists(options.InputPath))
            {
                throw new DirectoryNotFoundException($"Input directory '{options.InputPath}' does not exist.");
            }

            var logFiles = Directory.GetFiles(options.InputPath, options.Pattern, SearchOption.AllDirectories);
            Array.Sort(logFiles, StringComparer.OrdinalIgnoreCase);
            if (logFiles.Length == 0)
            {
                Console.Error.WriteLine($"No files matching '{options.Pattern}' found under '{options.InputPath}'.");
                return 1;
            }

            Console.WriteLine($"Decoding {logFiles.Length} files under {options.InputPath}");

            var samples = new List<SampleRecord>();
            var files = new List<FileSummary>();
            foreach (var logFile in logFiles)
            {
                var relativePath = GetRelativePath(options.InputPath, logFile);
                var decoded = new List<HarpLogMessage>();
                string error = null;
                try
                {
                    // Decoded eagerly so that a malformed tail is reported against the file rather
                    // than aborting the whole sweep. Messages read before the fault are kept.
                    decoded.AddRange(HarpBinaryLog.ReadMessages(logFile));
                }
                catch (InvalidDataException ex)
                {
                    error = ex.Message;
                }

                foreach (var message in decoded)
                {
                    samples.Add(new SampleRecord(null, null, relativePath, message));
                }

                var timestamps = decoded.Where(message => message.Timestamp.HasValue).ToArray();
                files.Add(new FileSummary(
                    relativePath,
                    decoded.Count,
                    decoded.Select(message => message.Address).Distinct().Count(),
                    decoded.Count(message => !message.ChecksumValid),
                    timestamps.Length > 0 ? timestamps.First().Timestamp : null,
                    timestamps.Length > 0 ? timestamps.Last().Timestamp : null,
                    error));
            }

            var samplesCsv = WriteSamples(options, samples);
            var summaryCsv = Path.Combine(options.OutputPath, "summary.csv");
            WriteCsv(summaryCsv, FileSummary.Header, files.Select(file => file.ToFields()));

            Console.WriteLine();
            Console.WriteLine("{0,10}  {1,10}  {2,10}  {3}", "Messages", "Addresses", "BadSums", "LogFile");
            foreach (var file in files)
            {
                Console.WriteLine(
                    "{0,10}  {1,10}  {2,10}  {3}",
                    file.Messages,
                    file.DistinctAddresses,
                    file.InvalidChecksums,
                    file.LogFile);
            }

            Console.WriteLine();
            Console.WriteLine($"Files: {files.Count}   Messages: {files.Sum(file => file.Messages)}");
            var faulted = files.Where(file => !string.IsNullOrEmpty(file.Error)).ToArray();
            foreach (var file in faulted)
            {
                Console.Error.WriteLine($"WARNING: {file.LogFile}: {file.Error}");
            }

            WriteChecksumWarning(samples);
            WritePaths(samplesCsv, summaryCsv, options.OutputPath, keepBinaries: false);
            return faulted.Length == 0 ? 0 : 1;
        }

        // ------------------------------------------------------------------ Running the workflow
        static int RunSweep(Options options)
        {
            var workflowDirectory = options.WorkflowDirectory ?? ResolveDefaultWorkflowDirectory();
            if (!Directory.Exists(workflowDirectory))
            {
                throw new DirectoryNotFoundException(
                    $"Workflow directory '{workflowDirectory}' does not exist. Build the solution first, " +
                    "or pass --workflow-directory.");
            }

            var samples = new List<SampleRecord>();
            var summary = new List<RunSummary>();

            foreach (var requested in options.Counts)
            {
                for (var repeat = 1; repeat <= options.Repeats; repeat++)
                {
                    var runPath = Path.Combine(options.OutputPath, $"count-{requested}", $"run-{repeat}");
                    if (Directory.Exists(runPath))
                    {
                        Directory.Delete(runPath, recursive: true);
                    }

                    Directory.CreateDirectory(runPath);
                    Console.WriteLine($"Running {options.WorkflowFileName} with Count={requested} (repeat {repeat} of {options.Repeats})");

                    var result = BonsaiWorkflowRunner.Run(
                        options.WorkflowFileName,
                        new Dictionary<string, string>
                        {
                            { "SubjectId", options.SubjectId },
                            { "SessionId", options.SessionId },
                            { "Path", runPath },
                            { "HarpLogName", options.LogName },
                            { "Count", requested.ToString(CultureInfo.InvariantCulture) }
                        },
                        workflowDirectory: workflowDirectory);

                    // Bonsai reports a zero exit code even when a workflow fails to build, so the
                    // captured error output is the only reliable signal that something went wrong.
                    if (!string.IsNullOrWhiteSpace(result.StandardError))
                    {
                        Console.Error.WriteLine(result.Describe());
                    }

                    var logFiles = Directory.GetFiles(runPath, "*.bin", SearchOption.AllDirectories);
                    Array.Sort(logFiles, StringComparer.OrdinalIgnoreCase);
                    var recorded = 0;
                    foreach (var logFile in logFiles)
                    {
                        foreach (var message in HarpBinaryLog.ReadMessages(logFile))
                        {
                            recorded++;
                            samples.Add(new SampleRecord(requested, repeat, GetRelativePath(runPath, logFile), message));
                        }
                    }

                    summary.Add(new RunSummary(requested, repeat, logFiles.Length, recorded));
                    if (!options.KeepBinaries)
                    {
                        TryDelete(runPath);
                    }
                }
            }

            var samplesCsv = WriteSamples(options, samples);
            var summaryCsv = Path.Combine(options.OutputPath, "summary.csv");
            WriteCsv(summaryCsv, RunSummary.Header, summary.Select(run => run.ToFields()));

            Console.WriteLine();
            Console.WriteLine("{0,6}  {1,4}  {2,9}  {3,9}  {4,8}  {5}", "Count", "Run", "LogFiles", "Recorded", "Missing", "Exact");
            foreach (var run in summary)
            {
                Console.WriteLine(
                    "{0,6}  {1,4}  {2,9}  {3,9}  {4,8}  {5}",
                    run.RequestedCount,
                    run.Run,
                    run.LogFiles,
                    run.RecordedSamples,
                    run.Missing,
                    run.Exact);
            }

            Console.WriteLine();
            foreach (var group in summary.GroupBy(run => run.RequestedCount).OrderBy(group => group.Key))
            {
                Console.WriteLine($"Count={group.Key} exact {group.Count(run => run.Exact)}/{group.Count()}");
            }

            WriteChecksumWarning(samples);
            WritePaths(samplesCsv, summaryCsv, options.OutputPath, options.KeepBinaries);
            return summary.All(run => run.Exact) ? 0 : 1;
        }

        // ------------------------------------------------------------------ Shared helpers
        /// <summary>
        /// Locates the test project build output, which sits beside this tool under the shared
        /// artifacts folder and holds both the workflows and the UclOpen extensions they need.
        /// </summary>
        static string ResolveDefaultWorkflowDirectory()
        {
            // artifacts/bin/UclOpen.HarpLogTool/<configuration>_<framework>
            var toolDirectory = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
            var configurationFolder = Path.GetFileName(toolDirectory);
            var binDirectory = Path.GetDirectoryName(Path.GetDirectoryName(toolDirectory));
            return Path.Combine(binDirectory, "UclOpen.Logging.Tests", configurationFolder);
        }

        static string GetRelativePath(string rootPath, string fileName)
        {
            var root = rootPath.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            return fileName.StartsWith(root, StringComparison.OrdinalIgnoreCase)
                ? fileName.Substring(root.Length)
                : fileName;
        }

        static string WriteSamples(Options options, List<SampleRecord> samples)
        {
            var samplesCsv = Path.Combine(options.OutputPath, "samples.csv");
            WriteCsv(samplesCsv, SampleRecord.Header, samples.Select(sample => sample.ToFields()));
            return samplesCsv;
        }

        static void WriteChecksumWarning(List<SampleRecord> samples)
        {
            var invalid = samples.Count(sample => !sample.Message.ChecksumValid);
            if (invalid > 0)
            {
                Console.Error.WriteLine($"WARNING: {invalid} decoded messages had an invalid checksum.");
            }
        }

        static void WritePaths(string samplesCsv, string summaryCsv, string outputPath, bool keepBinaries)
        {
            Console.WriteLine();
            Console.WriteLine($"Samples: {samplesCsv}");
            Console.WriteLine($"Summary: {summaryCsv}");
            if (keepBinaries)
            {
                Console.WriteLine($"Binaries kept under: {outputPath}");
            }
        }

        static void TryDelete(string path)
        {
            try
            {
                Directory.Delete(path, recursive: true);
            }
            catch (IOException)
            {
                // Leaving intermediate output behind should not fail the sweep.
            }
            catch (UnauthorizedAccessException)
            {
            }
        }

        static void WriteCsv(string fileName, IEnumerable<string> header, IEnumerable<IEnumerable<string>> rows)
        {
            using (var writer = new StreamWriter(fileName, append: false, encoding: new UTF8Encoding(false)))
            {
                writer.WriteLine(string.Join(",", header.Select(EscapeCsv)));
                foreach (var row in rows)
                {
                    writer.WriteLine(string.Join(",", row.Select(EscapeCsv)));
                }
            }
        }

        static string EscapeCsv(string value)
        {
            if (value == null)
            {
                return string.Empty;
            }

            if (value.IndexOfAny(new[] { ',', '"', '\r', '\n' }) < 0)
            {
                return value;
            }

            return "\"" + value.Replace("\"", "\"\"") + "\"";
        }
    }
}
