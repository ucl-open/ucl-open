from pathlib import Path
import json

from ucl_open.pyrat.session import SessionConfig

SCHEMA_ROOT = Path("./src/ucl_open/schemas")


def main():
    schema = SessionConfig.model_json_schema()
    Path(f"{SCHEMA_ROOT}/pyrat_session.json").write_text(json.dumps(schema, indent=2))


if __name__ == "__main__":
    main()
