using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Bonsai.IO;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace UclOpen.Logging
{
    public class JsonWriter : StreamSink<string, StreamWriter>
    {
        protected override StreamWriter CreateWriter(Stream stream)
        {
            return new StreamWriter(stream);
        }

        protected override void Write(StreamWriter writer, string input)
        {
            var parsed = JToken.Parse(input);
            var formatted = parsed.ToString(Formatting.Indented);
            writer.WriteLine(formatted);
        }
    }
}