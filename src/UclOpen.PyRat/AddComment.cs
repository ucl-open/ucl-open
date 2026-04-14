using Bonsai;
using System;
using System.ComponentModel;
using System.Reactive.Linq;

namespace UclOpen.Pyrat
{
    [Combinator]
    [Description("Appends a timestamped comment to the session config's Comments list.")]
    [WorkflowElementCategory(ElementCategory.Transform)]
    public class AddComment
    {
        [Description("The comment text to record.")]
        public string Content { get; set; } = "";

        public IObservable<SessionConfig> Process(IObservable<SessionConfig> source)
        {
            return source.Select(value =>
            {
                value.Comments.Add(new Comment
                {
                    Content = Content,
                    Created = DateTimeOffset.UtcNow
                });
                return value;
            });
        }
    }
}
