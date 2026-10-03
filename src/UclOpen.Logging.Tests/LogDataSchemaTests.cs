using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UclOpen.Tests;

namespace UclOpen.Logging.Tests
{
    [TestClass]
    public class LogDataSchemaTests : LoggingTestBase
    {
        // Double quotes do not survive being passed to the workflow as a -p argument, so the JSON
        // avoids string literals (and with them object keys) while still covering each value kind.
        const string MinimalJson = "[1,2.5,true,null,[],[0]]";

        protected override string WorkflowFileName => "LogDataSchemaTest.bonsai";

        [DataTestMethod]
        [DataRow("Schema")]
        [DataRow("TestSchema")]
        public void LogDataSchema_MinimalJson_WritesJsonToNamedLog(string logName)
        {
            var result = RunWorkflow(logName, MinimalJson);
            var logFile = GetSingleLogFile("*.json", result);

            var logFileName = Path.GetFileName(logFile);
            Assert.IsTrue(
                logFileName.StartsWith(logName, StringComparison.Ordinal),
                $"Expected the log file name '{logFileName}' to be prefixed with the requested " +
                $"Name '{logName}'.{result.Describe()}");

            // The writer reformats its input, so the log is compared by structure rather than text.
            var contents = File.ReadAllText(logFile);
            JToken logged;
            try
            {
                logged = JToken.Parse(contents);
            }
            catch (JsonReaderException ex)
            {
                Assert.Fail($"Expected '{logFile}' to hold valid JSON but found '{contents}' ({ex.Message})." +
                    result.Describe());
                return;
            }

            var expected = JToken.Parse(MinimalJson);
            Assert.IsTrue(
                JToken.DeepEquals(expected, logged),
                $"Expected '{logFile}' to hold the JSON written in, '{expected.ToString(Formatting.None)}', " +
                $"but found '{logged.ToString(Formatting.None)}'.{result.Describe()}");
        }

        [TestMethod]
        public void LogDataSchema_MinimalJson_WritesExpectedDirectoryStructure()
        {
            const string LogName = "Schema";
            var result = RunWorkflow(LogName, MinimalJson);
            var logFile = GetSingleLogFile("*.json", result);

            var segments = AssertSessionFolders(logFile, result);
            Assert.AreEqual(
                2,
                segments.Length,
                $"Expected the log to sit one folder below the session folder, but found " +
                $"'{string.Join(Path.DirectorySeparatorChar.ToString(), segments)}'.{result.Describe()}");

            Assert.AreEqual(
                LogName,
                segments[0],
                $"Expected the log subfolder to be named after Name.{result.Describe()}");

            StringAssert.Matches(
                segments[1],
                new Regex($@"^{Regex.Escape(LogName)}_.+\.json$"),
                $"Expected the JSON file to sit inside the '{LogName}' folder and be prefixed with " +
                $"it.{result.Describe()}");
        }

        BonsaiWorkflowResult RunWorkflow(string logName, string json)
        {
            return RunWorkflow(new Dictionary<string, string>
            {
                { "Name", logName },
                { "Json", json }
            });
        }
    }
}
