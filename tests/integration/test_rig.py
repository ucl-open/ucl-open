from ucl_open.core.rig import Rig
from ucl_open.devices.arduino import LedController, LedDriver
from ucl_open.devices.behavior_board import BehaviorBoard
from ucl_open.devices.lick_spout_stage import LickSpoutStageDriver, SpoutRigPosition
from ucl_open.devices.lickety_split import LicketySplit
from ucl_open.vision.displays import Screen


class DummyRig(Rig):
    led_driver: LedDriver
    behavior_board: BehaviorBoard
    lick_spout: LickSpoutStageDriver
    lickety_split: LicketySplit
    screen: Screen


def test_rig_validate():
    rig = DummyRig(
        root_path="data",
        led_driver=LedDriver(
            port_name="COM5", sampling_interval=10, led_controller=LedController(digital_out_pin=8)
        ),
        behavior_board=BehaviorBoard(port_name="COM3"),
        lick_spout=LickSpoutStageDriver(port_name="COM2", set_position=SpoutRigPosition()),
        lickety_split=LicketySplit(port_name="COM1"),
        screen=Screen(),
    )
    assert rig.root_path == "data"
