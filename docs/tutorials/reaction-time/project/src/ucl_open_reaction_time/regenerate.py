from pathlib import Path
from typing import Union

import pydantic
from aind_behavior_services.schema import BonsaiSgenSerializers, convert_pydantic_to_bonsai
from ucl_open.core.experiment import ExperimentSession

import ucl_open_reaction_time.rig
import ucl_open_reaction_time.task

SCHEMA_ROOT = Path("./src/DataSchemas/")
EXTENSIONS_ROOT = Path("./src/Extensions/")
NAMESPACE_PREFIX = "UclOpenReactionTimeDataSchema"

def main():
    models = [
        ucl_open_reaction_time.task.UclOpenReactionTimeTaskLogic,
        ucl_open_reaction_time.rig.UclOpenReactionTimeRig,
        ExperimentSession
    ]
    model = pydantic.RootModel[Union[tuple(models)]]

    convert_pydantic_to_bonsai(
        model, # type: ignore
        model_name="ucl_open_reaction_time",
        root_element="Root",
        cs_namespace=NAMESPACE_PREFIX,
        json_schema_output_dir=SCHEMA_ROOT,
        cs_output_dir=EXTENSIONS_ROOT,
        cs_serializer=[BonsaiSgenSerializers.JSON],
    )


if __name__ == "__main__":
    main()