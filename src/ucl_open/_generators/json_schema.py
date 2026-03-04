import logging
import os
from pathlib import Path
from ucl_open.rigs.base import BaseSchema
from ucl_open.rigs.data_types import DataTypes
from ucl_open.rigs.displays import Displays
from typing import Union
import json
import pydantic

SCHEMA_ROOT = Path("./src/ucl_open/schemas")

def main():
    models = [
        DataTypes,
        Displays
    ]
    model = pydantic.RootModel[Union[tuple(models)]]
    
    schema = model.model_json_schema(union_format="primitive_type_array")
    schema.pop("properties", None)
    Path(f"{SCHEMA_ROOT}/data_types.json").write_text(json.dumps(schema, indent=2))
    
    
if __name__ == "__main__":
    main()