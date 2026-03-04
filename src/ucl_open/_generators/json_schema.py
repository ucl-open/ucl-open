import logging
import os
from pathlib import Path
from ucl_open.rigs.base import BaseSchema
from ucl_open.rigs.data_types import DataTypes
from typing import Type

SCHEMA_ROOT = Path("./schema")

model: Type[BaseSchema] = DataTypes

schema = model.model_json_schema(union_format="primitive_type_array")

print(schema)