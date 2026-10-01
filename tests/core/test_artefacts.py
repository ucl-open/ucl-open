from typing import Dict, List

from pydantic import BaseModel, Field

from ucl_open.core.artefacts import SCHEMA_TAG, ArtefactPath, rig_artefacts
from ucl_open.core.rig import Rig


class Sensor(BaseModel):
    curve: ArtefactPath = Field(description="Required reference.")
    filter: ArtefactPath | None = Field(default=None, description="Optional reference.")
    label: str = Field(default="sensor", description="Not a reference.")


class Bench(BaseModel):
    main: Sensor
    spares: List[Sensor] = Field(default=[])
    named: Dict[str, Sensor] = Field(default={})


def test_bare_rig_references_nothing():
    assert rig_artefacts(Rig(root_path="C:\\Data")) == {}


def test_required_and_optional_references_are_found_unset_ones_skipped():
    bench = Bench(main=Sensor(curve="calibration/main.json"))
    assert rig_artefacts(bench) == {"main.curve": "calibration/main.json"}


def test_lists_and_dictionaries_are_walked():
    bench = Bench(
        main=Sensor(curve="a.json", filter="b.json"),
        spares=[Sensor(curve="c.json")],
        named={"left": Sensor(curve="d.json")},
    )
    assert rig_artefacts(bench) == {
        "main.curve": "a.json",
        "main.filter": "b.json",
        "spares[0].curve": "c.json",
        "named.left.curve": "d.json",
    }


def test_plain_strings_are_not_references():
    assert "main.label" not in rig_artefacts(Bench(main=Sensor(curve="a.json")))


def test_schema_tags_references_and_keeps_them_strings():
    properties = Sensor.model_json_schema()["properties"]
    assert properties["curve"]["type"] == "string"
    assert properties["curve"][SCHEMA_TAG] is True
    assert "label" in properties and SCHEMA_TAG not in properties["label"]
