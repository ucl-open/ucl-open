import os

from ucl_open.core import Vector3
from ucl_open.devices.harp import HarpHobgoblin
from ucl_open.vision import DisplayCalibration, DisplayExtrinsics, DisplayIntrinsics, Screen, ViewportConfiguration

from ucl_open_reaction_time.rig import UclOpenReactionTimeRig

rig = UclOpenReactionTimeRig(
    root_path="../temp_data",
    harp_hobgoblin=HarpHobgoblin(port_name="COM7"),
    screen=Screen(
        window_width=1000,
        window_height=1000,
        calibration={
            "main": DisplayCalibration(
                extrinsics=DisplayExtrinsics(
                    rotation=Vector3(x=0.0, y=0.0, z=0.0),
                    translation=Vector3(x=0.0, y=1.309016, z=-13.27)
                ),
                intrinsics=DisplayIntrinsics(
                    viewport_configuration=ViewportConfiguration(),
                    display_width=20,
                    display_height=15
                )
            )
        }
    )
)

def main(path_seed: str = "./local/{schema}.json"):
    os.makedirs(os.path.dirname(path_seed), exist_ok=True)
    models = [rig]

    for model in models:
        with open(path_seed.format(schema=model.__class__.__name__), "w", encoding="utf-8") as f:
            f.write(model.model_dump_json(indent=2, by_alias=True))


if __name__ == "__main__":
    main()