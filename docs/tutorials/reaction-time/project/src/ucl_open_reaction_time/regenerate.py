import json
from pathlib import Path
from typing import Union

import pydantic
from ucl_open.core.experiment import ExperimentSession

import ucl_open_reaction_time.rig
import ucl_open_reaction_time.task

SCHEMA_ROOT = Path("./src/DataSchemas/")
SCHEMA_FILE = SCHEMA_ROOT / "ucl-open-reaction-time.json"

def main():
    models = [
        ucl_open_reaction_time.task.UclOpenReactionTimeTaskLogic,
        ucl_open_reaction_time.rig.UclOpenReactionTimeRig,
        ExperimentSession
    ]
    model = pydantic.RootModel[Union[tuple(models)]]
    schema = model.model_json_schema(by_alias=True, mode="serialization", union_format="primitive_type_array")
    SCHEMA_ROOT.mkdir(parents=True, exist_ok=True)
    SCHEMA_FILE.write_text(json.dumps(schema, indent=2))
    print(f"Schema written to {SCHEMA_FILE}")


if __name__ == "__main__":
    main()