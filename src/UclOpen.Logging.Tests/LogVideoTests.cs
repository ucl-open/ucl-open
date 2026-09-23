using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using OpenCV.Net;
using Capture = OpenCV.Net.Capture;
using UclOpen.Tests;

namespace UclOpen.Logging.Tests
{
    [TestClass]
    public class LogVideoTests
    {
        const string WorkflowFileName = "LogVideoTest.bonsai";
        const string SubjectId = "TestSubject";
        const string SessionId = "001";
        const double SourceFrameRate = 30;

        // Solid frames survive the lossy codec almost unchanged, but each encode can still shift the
        // mean of a channel by a few levels, and the logged video has been encoded twice.
        const double ColorTolerance = 12;

        static readonly string[] ExpectedHeader = { "Seconds", "Value.Width", "Value.Height" };

        string testRoot;
        string logRoot;
        string sourceVideo;

        [TestInitialize]
        public void TestInitialize()
        {
            // Log outside the repository so that a failed run never leaves files in the working tree.
            // The source video sits beside the log root so that it is never mistaken for a log.
            testRoot = Path.Combine(Path.GetTempPath(), "UclOpen.Logging.Tests", Guid.NewGuid().ToString("N"));
            logRoot = Path.Combine(testRoot, "logs");
            sourceVideo = Path.Combine(testRoot, "source.avi");
            Directory.CreateDirectory(logRoot);
        }

        [TestCleanup]
        public void TestCleanup()
        {
            if (testRoot == null || !Directory.Exists(testRoot))
            {
                return;
            }

            try
            {
                Directory.Delete(testRoot, recursive: true);
            }
            catch (IOException)
            {
                // Leaving a stray temp directory behind should not fail the run.
            }
            catch (UnauthorizedAccessException)
            {
            }
        }

        // The workflow default LogName is "Video", so at least one row must differ from it to prove
        // the value is actually being applied rather than coincidentally matching. Frame sizes are
        // kept at 160x120 or above, since the FMP4 encoder writes unreadable videos at e.g. 64x48.
        [DataTestMethod]
        [DataRow("TestVideo", 10, 320, 240)]
        [DataRow("Video", 25, 160, 120)]
        public void LogRawVideo_FileCapture_WritesEveryFrameToVideoAndMetadata(
            string logName,
            int frameCount,
            int width,
            int height)
        {
            var colors = GenerateSourceVideo(frameCount, width, height);
            var result = RunWorkflow(logName);
            var logFiles = GetLogFiles(result);

            var frames = ReadFrameColors(logFiles.Video, width, height, result);
            Assert.AreEqual(
                frameCount,
                frames.Count,
                $"Expected every frame of the source video to be written to '{logFiles.Video}'." +
                result.Describe());

            // Each source frame is a distinct solid color, so matching them in order shows that no
            // frames were dropped, duplicated or reordered along the way.
            for (var frame = 0; frame < frameCount; frame++)
            {
                for (var channel = 0; channel < 3; channel++)
                {
                    var expected = GetChannel(colors[frame], channel);
                    var actual = GetChannel(frames[frame], channel);
                    Assert.IsTrue(
                        Math.Abs(expected - actual) <= ColorTolerance,
                        $"Expected channel {channel} of frame {frame} to be close to {expected} but found " +
                        $"{actual:F1}.{result.Describe()}");
                }
            }

            var lines = File.ReadAllLines(logFiles.Metadata);
            Assert.AreEqual(
                frameCount + 1,
                lines.Length,
                $"Expected a single header row followed by one row per frame in '{logFiles.Metadata}'." +
                result.Describe());

            CollectionAssert.AreEqual(
                ExpectedHeader,
                lines[0].Split(','),
                $"Unexpected header row in '{logFiles.Metadata}'.{result.Describe()}");

            var previousSeconds = double.NegativeInfinity;
            for (var frame = 0; frame < frameCount; frame++)
            {
                var line = lines[frame + 1];
                var columns = line.Split(',');
                Assert.AreEqual(
                    ExpectedHeader.Length,
                    columns.Length,
                    $"Unexpected column count in frame {frame} ('{line}').{result.Describe()}");

                Assert.IsTrue(
                    double.TryParse(columns[0], NumberStyles.Float, CultureInfo.InvariantCulture, out var seconds),
                    $"Expected '{ExpectedHeader[0]}' in frame {frame} to be a number but found " +
                    $"'{columns[0]}'.{result.Describe()}");

                // The test time base only ever counts up, so the frame timestamps must too.
                Assert.IsTrue(
                    seconds >= previousSeconds,
                    $"Expected '{ExpectedHeader[0]}' to be non-decreasing, but frame {frame} has {seconds} " +
                    $"after {previousSeconds}.{result.Describe()}");
                previousSeconds = seconds;

                AssertIntegerColumn(columns, 1, width, frame, result);
                AssertIntegerColumn(columns, 2, height, frame, result);
            }
        }

        [TestMethod]
        public void LogRawVideo_FileCapture_WritesExpectedDirectoryStructure()
        {
            const string LogName = "TestVideo";
            GenerateSourceVideo(frameCount: 5, width: 160, height: 120);
            var result = RunWorkflow(LogName);
            var logFiles = GetLogFiles(result);

            // The video and its metadata describe the same frames, so they are expected to be
            // written side by side under one name, differing only by extension.
            Assert.AreEqual(
                Path.ChangeExtension(logFiles.Video, null),
                Path.ChangeExtension(logFiles.Metadata, null),
                $"Expected the video and metadata logs to share a folder and base name.{result.Describe()}");

            var relativePath = logFiles.Video.Substring(logRoot.Length).TrimStart(Path.DirectorySeparatorChar);
            var segments = relativePath.Split(Path.DirectorySeparatorChar);
            Assert.AreEqual(
                4,
                segments.Length,
                $"Expected the logs to sit three folders deep below the log root, but found " +
                $"'{relativePath}'.{result.Describe()}");

            Assert.AreEqual(
                $"sub-{SubjectId}",
                segments[0],
                $"Expected the subject folder to be named sub-<subject>.{result.Describe()}");

            // LogController lays out the session folder as ses-<session>_date-<datetime>, where the
            // datetime is a round-trip UTC timestamp with the time separators replaced.
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
                    out var sessionDate),
                $"Could not parse the session date from '{sessionFolder}'.{result.Describe()}");

            // Guards against the session folder picking up a fixed epoch rather than the run time.
            var age = DateTime.UtcNow - sessionDate;
            Assert.IsTrue(
                age > TimeSpan.FromMinutes(-10) && age < TimeSpan.FromMinutes(10),
                $"Expected the session date '{sessionDate:O}' to be close to the time of the run " +
                $"({DateTime.UtcNow:O}).{result.Describe()}");

            Assert.AreEqual(
                LogName,
                segments[2],
                $"Expected the log subfolder to be named after LogName.{result.Describe()}");

            StringAssert.Matches(
                segments[3],
                new Regex($@"^{Regex.Escape(LogName)}_.+\.avi$"),
                $"Expected the video file to sit inside the '{LogName}' folder and be prefixed with " +
                $"it.{result.Describe()}");
        }

        /// <summary>
        /// Writes a video of solid, randomly colored frames to the source path, and returns the
        /// color of each frame in BGR order.
        /// </summary>
        Scalar[] GenerateSourceVideo(int frameCount, int width, int height)
        {
            // Seeded so that a failing run can be reproduced exactly.
            var random = new Random(frameCount);
            var colors = new Scalar[frameCount];
            var size = new Size(width, height);
            using (var writer = new VideoWriter(sourceVideo, VideoWriter.FourCC('F', 'M', 'P', '4'), SourceFrameRate, size))
            using (var image = new IplImage(size, IplDepth.U8, 3))
            {
                for (var frame = 0; frame < frameCount; frame++)
                {
                    colors[frame] = Scalar.Rgb(random.Next(256), random.Next(256), random.Next(256));
                    image.Set(colors[frame]);
                    writer.WriteFrame(image);
                }
            }

            // Confirms the fixture itself is sound, so a failure later on points at the logger.
            var decodedFrames = 0;
            using (var capture = Capture.CreateFileCapture(sourceVideo))
            {
                Assert.IsNotNull(capture, $"Could not open the generated source video '{sourceVideo}'.");
                while (capture.QueryFrame() != null)
                {
                    decodedFrames++;
                }
            }

            Assert.AreEqual(
                frameCount,
                decodedFrames,
                $"Expected the generated source video '{sourceVideo}' to decode to every frame written.");
            return colors;
        }

        /// <summary>
        /// Decodes every frame of a video, checking its size and returning its mean color.
        /// </summary>
        static List<Scalar> ReadFrameColors(string fileName, int width, int height, BonsaiWorkflowResult result)
        {
            var colors = new List<Scalar>();
            using (var capture = Capture.CreateFileCapture(fileName))
            {
                Assert.IsNotNull(capture, $"Could not open '{fileName}' for reading.{result.Describe()}");

                // Frames returned by the capture are owned by it and must not be disposed here.
                IplImage image;
                while ((image = capture.QueryFrame()) != null)
                {
                    Assert.AreEqual(
                        new Size(width, height),
                        image.Size,
                        $"Unexpected size of frame {colors.Count} in '{fileName}'.{result.Describe()}");
                    colors.Add(CV.Avg(image));
                }
            }

            return colors;
        }

        static double GetChannel(Scalar scalar, int channel)
        {
            switch (channel)
            {
                case 0: return scalar.Val0;
                case 1: return scalar.Val1;
                case 2: return scalar.Val2;
                default: return scalar.Val3;
            }
        }

        static void AssertIntegerColumn(string[] columns, int column, int expected, int frame, BonsaiWorkflowResult result)
        {
            Assert.IsTrue(
                int.TryParse(columns[column], NumberStyles.Integer, CultureInfo.InvariantCulture, out var value),
                $"Expected '{ExpectedHeader[column]}' in frame {frame} to be an integer but found " +
                $"'{columns[column]}'.{result.Describe()}");
            Assert.AreEqual(
                expected,
                value,
                $"Unexpected '{ExpectedHeader[column]}' in frame {frame}.{result.Describe()}");
        }

        BonsaiWorkflowResult RunWorkflow(string logName)
        {
            return BonsaiWorkflowRunner.Run(WorkflowFileName, new Dictionary<string, string>
            {
                { "SubjectId", SubjectId },
                { "SessionId", SessionId },
                { "Path", logRoot },
                { "FileName", sourceVideo },
                // Played back in real time, since frames read faster than the time base ticks would
                // have no timestamp to pair with and be dropped before reaching the logger.
                { "PlaybackRate", SourceFrameRate.ToString(CultureInfo.InvariantCulture) },
                { "LogName", logName }
            });
        }

        (string Video, string Metadata) GetLogFiles(BonsaiWorkflowResult result)
        {
            // The log file names embed a timestamp, so search for them rather than reconstructing the paths.
            return (GetSingleLogFile("*.avi", result), GetSingleLogFile("*.csv", result));
        }

        string GetSingleLogFile(string searchPattern, BonsaiWorkflowResult result)
        {
            var logFiles = Directory.GetFiles(logRoot, searchPattern, SearchOption.AllDirectories);
            Assert.AreEqual(
                1,
                logFiles.Length,
                $"Expected the workflow to write exactly one '{searchPattern}' log file under '{logRoot}'." +
                result.Describe());
            return logFiles[0];
        }
    }
}
