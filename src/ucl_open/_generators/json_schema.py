from pathlib import Path
from typing import Union
import json
import pydantic

import ucl_open.core.data_types as _core_dt
import ucl_open.devices.data_types as _dev_dt


def _collect_fields(*modules):
    fields = {}
    for mod in modules:
        for name in getattr(mod, "__all__", []):
            cls = getattr(mod, name)
            if isinstance(cls, type):
                fields[name] = (cls, ...)
    return fields


DataTypes = pydantic.create_model("DataTypes", **_collect_fields(_core_dt, _dev_dt))

SCHEMA_ROOT = Path("./src/ucl_open/schemas")


def main():
    models = [DataTypes]
    model = pydantic.RootModel[Union[tuple(models)]]

    schema = model.model_json_schema(union_format="primitive_type_array")
    schema.pop("properties", None)
    Path(f"{SCHEMA_ROOT}/data_types.json").write_text(json.dumps(schema, indent=2))


if __name__ == "__main__":
    main()
