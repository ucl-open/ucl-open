using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using UclOpenReactionTime;
using Bonsai.Vision;
using OpenCV.Net;

[Combinator]
[Description("")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class ConvertCalibration
{
    public IObservable<Dictionary<string, Tuple<Point3d, Point3d, double, double, Point2d, Point2d>>> Process(IObservable<Dictionary<string, DisplayCalibration>> source)
    {
        return source.Select(value => {
            var convertedDict = new Dictionary<string, Tuple<Point3d, Point3d, double, double, Point2d, Point2d>>();
            foreach (KeyValuePair<string, DisplayCalibration> kvp in value)
            {
                convertedDict.Add(
                    kvp.Key,
                    new Tuple<Point3d, Point3d, double, double, Point2d, Point2d>(
                        new Point3d (kvp.Value.Extrinsics.Rotation.X, kvp.Value.Extrinsics.Rotation.Y, kvp.Value.Extrinsics.Rotation.Z),
                        new Point3d (kvp.Value.Extrinsics.Translation.X, kvp.Value.Extrinsics.Translation.Y, kvp.Value.Extrinsics.Translation.Z),
                        kvp.Value.Intrinsics.DisplayHeight,
                        kvp.Value.Intrinsics.DisplayWidth,
                        new Point2d (kvp.Value.Intrinsics.ViewportConfiguration.Width, kvp.Value.Intrinsics.ViewportConfiguration.Height),
                        new Point2d (kvp.Value.Intrinsics.ViewportConfiguration.X, kvp.Value.Intrinsics.ViewportConfiguration.Y)
                    )
                );
            }
            return convertedDict;
        });
    }
}
