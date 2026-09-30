import pytest
from pydantic import ValidationError

from ucl_open.core import yaml as rig_yaml
from ucl_open.devices.behavior_board import (
    BehaviorBoard,
    CalibratedPulse,
    FixedPulse,
    PulseController,
    PulseOutput,
    PulseOutputs,
)


def outputs() -> PulseOutputs:
    return PulseOutputs(
        DO1=PulseOutput(CalibratedPulse(artefact="calibration/valve-DO1.json")),
        DO2=PulseOutput(CalibratedPulse(artefact="calibration/valve-DO2.json")),
        DO3=PulseOutput(FixedPulse(pulse_width_ms=5)),
    )


def test_each_line_carries_one_source():
    out = outputs()
    assert isinstance(out.do1.root, CalibratedPulse)
    assert isinstance(out.do3.root, FixedPulse)
    assert out.do3.root.pulse_width_ms == 5


def test_every_line_is_required():
    with pytest.raises(ValidationError):
        PulseOutputs(
            DO1=PulseOutput(FixedPulse(pulse_width_ms=40)),
            DO2=PulseOutput(FixedPulse(pulse_width_ms=40)),
        )


def test_source_is_chosen_by_discriminator_in_yaml(tmp_path):
    path = tmp_path / "board.yml"
    path.write_text(
        "portName: COM3\n"
        "pulseController:\n"
        "  outputs:\n"
        "    DO1: {discriminatorType: CalibratedPulse, artefact: calibration/valve-DO1.json}\n"
        "    DO2: {discriminatorType: FixedPulse, pulseWidthMs: 30}\n"
        "    DO3: {discriminatorType: FixedPulse, pulseWidthMs: 5}\n",
        encoding="utf-8",
    )
    board = rig_yaml.load(BehaviorBoard, path)
    assert isinstance(board.pulse_controller.outputs.do1.root, CalibratedPulse)
    assert board.pulse_controller.outputs.do2.root.pulse_width_ms == 30


def test_a_source_cannot_mix_fields():
    with pytest.raises(ValidationError):
        PulseOutputs.model_validate(
            {
                "DO1": {"discriminatorType": "FixedPulse", "artefact": "calibration/valve.json"},
                "DO2": {"discriminatorType": "FixedPulse", "pulseWidthMs": 1},
                "DO3": {"discriminatorType": "FixedPulse", "pulseWidthMs": 0},
            }
        )


def test_unknown_source_is_rejected():
    with pytest.raises(ValidationError):
        PulseOutputs.model_validate(
            {
                "DO1": {"discriminatorType": "Valve", "pulseWidthMs": 1},
                "DO2": {"discriminatorType": "FixedPulse", "pulseWidthMs": 1},
                "DO3": {"discriminatorType": "FixedPulse", "pulseWidthMs": 0},
            }
        )


def test_round_trips_through_yaml(tmp_path):
    board = BehaviorBoard(port_name="COM3", pulse_controller=PulseController(outputs=outputs()))
    path = tmp_path / "board.yml"
    rig_yaml.save(board, path)
    # Compare dumps: swc BaseSchema keeps a _container back-reference, so == on nested models recurses.
    assert rig_yaml.load(BehaviorBoard, path).model_dump() == board.model_dump()


def test_schema_exposes_the_union_as_a_named_definition():
    defs = BehaviorBoard.model_json_schema(by_alias=True)["$defs"]
    union = defs["PulseOutput"]
    assert set(union["discriminator"]["mapping"]) == {"FixedPulse", "CalibratedPulse"}
    assert set(defs["PulseOutputs"]["required"]) == {"DO1", "DO2", "DO3"}
