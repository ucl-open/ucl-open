# Bonsai Implementation

### Creating Configurations
The experiment schemas we have created already define the available parameters to set to control our experiment, next we need to create concrete definitions for these parameters that will be loaded into Bonsai. The `ucl-open` template has example scripts for generating these definitions in the `examples` folder.

### Session
In `experiment\session.py` we can see the script for generating the session metadata. When generated fresh from the template it should have some error warnings as we have not filled in the required fields. Fill these in for an example session:
```
import datetime
import os
import git

# from swc.aeon.schema import Experiment
from ucl_open.rigs.experiment import Experiment

# TODO - autofill experiment fields
session = Experiment(
    subject_id="Plimbo",
    workflow="main.bonsai",
    commit=git.Repo(search_parent_directories=True).head.object.hexsha,
    repository_url=""
)

def main(path_seed: str = "./local/{schema}.json"):
    os.makedirs(os.path.dirname(path_seed), exist_ok=True)
    models = [session]

    for model in models:
        with open(path_seed.format(schema=model.__class__.__name__), "w", encoding="utf-8") as f:
            f.write(model.model_dump_json(indent=2, by_alias=True))


if __name__ == "__main__":
    main()
```
I've left the `repository_url` blank, this can be filled in with the correct url if you have a remote repository already set up. I also use the git library to automatically populate the commit hash in this example. Run the script with:
```
uv run examples\session.py
```
You should see a file `Experiment.json` show up in the `local` folder. This is the actual session settings file that will be loaded and deserialized by Bonsai.

### Rig
We'll repeat the process for the rig configuration in `examples\rig.py`:
```
import os

from ucl_open_implementation_example.rig import (
    UclOpenImplementationExampleRig
)

from ucl_open.rigs.harp import HarpHobgoblin
from ucl_open.rigs.device import Screen

rig = UclOpenImplementationExampleRig(
    harp_hobgoblin=HarpHobgoblin(port_name="COM4"),
    screen=Screen()
)

def main(path_seed: str = "./local/{schema}.json"):
    os.makedirs(os.path.dirname(path_seed), exist_ok=True)
    models = [rig]

    for model in models:
        with open(path_seed.format(schema=model.__class__.__name__), "w", encoding="utf-8") as f:
            f.write(model.model_dump_json(indent=2, by_alias=True))


if __name__ == "__main__":
    main()
```
We don't need to do much here except import the `HarpHobgoblin` schema from `ucl_open_rigs` and create an instance inside the rig definition with the USB connection COM port for our machine. At this stage we'll use the default settings for `Screen` so we don't assign any non-default parameters. Run this script with:
```
uv run examples\rig.py
```