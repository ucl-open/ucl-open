using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using UclOpen.Tests;

namespace UclOpen.Logging.Tests
{
    [TestClass]
    public class LogHarpTests
    {
        const string WorkflowFileName = "LogHarpTest.bonsai";
        const string SubjectId = "TestSubject";
        const string SessionId = "001";

        string logRoot;

        [TestInitialize]
        public void TestInitialize()
        {
            // Log outside the repository so that a failed run never leaves files in the working tree.
            logRoot = Path.Combine(Path.GetTempPath(), "UclOpen.Logging.Tests", Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(logRoot);
        }

        [TestCleanup]
        public void TestCleanup()
        {
            if (logRoot == null || !Directory.Exists(logRoot))
            {
                return;
            }

            try
            {
                Directory.Delete(logRoot, recursive: true);
            }
            catch (IOException)
            {
                // Leaving a stray temp directory behind should not fail the run.
            }
            catch (UnauthorizedAccessException)
            {
            }
        }

        [TestMethod]
        public void LogHarpDevice_SimulatedBehavior_WritesExpectedDirectoryStructure()
        {
            const string LogName = "SimulatedBehavior";
            // Deliberately a small count. Logging is currently unreliable once several registers are
            // written concurrently, so a larger count would make this structural check flaky for
            // reasons that have nothing to do with the layout it is verifying.
            var result = RunWorkflow(LogName, count: 3);
            var logFiles = GetLogFiles(result);

            // Every register of the device shares a single folder named after the device.
            var deviceFolders = logFiles
                .Select(Path.GetDirectoryName)
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToArray();
            Assert.AreEqual(
                1,
                deviceFolders.Length,
                $"Expected every register log to share one device folder, but found " +
                $"{deviceFolders.Length}: {string.Join(", ", deviceFolders)}.{result.Describe()}");

            var relativePath = deviceFolders[0].Substring(logRoot.Length).TrimStart(Path.DirectorySeparatorChar);
            var segments = relativePath.Split(Path.DirectorySeparatorChar);
            Assert.AreEqual(
                3,
                segments.Length,
                $"Expected the device folder to sit two folders below the log root, but found " +
                $"'{relativePath}'.{result.Describe()}");

            Assert.AreEqual(
                $"sub-{SubjectId}",
                segments[0],
                $"Expected the subject folder to be named sub-<subject>.{result.Describe()}");

            // LogController lays out the session folder as ses-<session>_date-<datetime>.
            var sessionFolder = segments[1];
            var sessionMatch = Regex.Match(
                sessionFolder,
                $@"^ses-{Regex.Escape(SessionId)}_date-(\d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}-\d{{2}}-\d{{2}})$");
            Assert.IsTrue(
                sessionMatch.Success,
                $"Expected the session folder to match ses-{SessionId}_date-<datetime> but found " +
                $"'{sessionFolder}'.{result.Describe()}");

            Assert.IsTrue(
                DateTime.TryParseExact(
                    sessionMatch.Groups[1].Value,
                    "yyyy-MM-ddTHH-mm-ss",
                    CultureInfo.InvariantCulture,
                    DateTimeStyles.None,
                    out _),
                $"Could not parse the session date from '{sessionFolder}'.{result.Describe()}");

            Assert.AreEqual(
                LogName,
                segments[2],
                $"Expected the device folder to be named after LogName.{result.Describe()}");

            // Each register still gets its own file, distinguished by the register address.
            foreach (var logFile in logFiles)
            {
                var address = GetRegisterAddress(logFile, LogName, result);
                Assert.IsTrue(
                    BehaviorDeviceSimulator.Registers.Any(register => register.Address == address),
                    $"Address {address} in '{Path.GetFileName(logFile)}' is not a register of the " +
                    $"simulated device.{result.Describe()}");
            }

            var addresses = logFiles.Select(logFile => GetRegisterAddress(logFile, LogName, result)).ToArray();
            CollectionAssert.AllItemsAreUnique(
                addresses,
                $"Expected one log file per register address.{result.Describe()}");
        }

        // Counts of one to three are currently reliable; from around five the logger starts losing
        // whole register logs, so the larger rows are expected to fail until that is fixed. The
        // small rows are kept to guard the cases that do work.
        [DataTestMethod]
        [DataRow("SimulatedBehavior", 1)]
        [DataRow("SimulatedBehavior", 3)]
        [DataRow("SimulatedBehavior", 20)]
        [DataRow("TestHarp", 100)]
        public void LogHarpDevice_SimulatedBehavior_WritesRequestedSampleCountAcrossRegisters(
            string logName,
            int count)
        {
            var result = RunWorkflow(logName, count);
            var logFiles = GetLogFiles(result);

            // Each register is logged to its own file, so the requested Count is spread across the
            // per-register logs rather than landing in any single one.
            var samplesPerRegister = logFiles.ToDictionary(
                logFile => GetRegisterAddress(logFile, logName, result),
                HarpBinaryLog.CountMessages);
            var totalSamples = samplesPerRegister.Values.Sum();

            var breakdown = string.Join(
                ", ",
                samplesPerRegister.OrderBy(entry => entry.Key).Select(entry => $"{entry.Key}={entry.Value}"));
            Assert.AreEqual(
                count,
                totalSamples,
                $"Expected the samples across all register logs to add up to the requested Count. " +
                $"Found {logFiles.Length} logs: {breakdown}.{result.Describe()}");
        }

        int GetRegisterAddress(string logFile, string logName, BonsaiWorkflowResult result)
        {
            // Log files are named <LogName>_<address>_<timestamp>, where the timestamp is appended
            // by the writer rather than being part of the register name.
            var fileName = Path.GetFileName(logFile);
            var match = Regex.Match(fileName, $@"^{Regex.Escape(logName)}_(\d+)_");
            Assert.IsTrue(
                match.Success,
                $"Expected the log file name '{fileName}' to match {logName}_<address>_<timestamp>." +
                result.Describe());
            return int.Parse(match.Groups[1].Value, CultureInfo.InvariantCulture);
        }

        BonsaiWorkflowResult RunWorkflow(string logName, int count)
        {
            return BonsaiWorkflowRunner.Run(WorkflowFileName, new Dictionary<string, string>
            {
                { "SubjectId", SubjectId },
                { "SessionId", SessionId },
                { "Path", logRoot },
                // The workflow externalizes LogHarpDevice's LogName under this display name.
                { "HarpLogName", logName },
                { "Count", count.ToString(CultureInfo.InvariantCulture) }
            });
        }

        string[] GetLogFiles(BonsaiWorkflowResult result)
        {
            var logFiles = Directory.GetFiles(logRoot, "*.bin", SearchOption.AllDirectories);
            Assert.AreNotEqual(
                0,
                logFiles.Length,
                $"Expected the workflow to write at least one Harp log under '{logRoot}'.{result.Describe()}");
            return logFiles;
        }
    }
}
