
from devices import HVChannel, LEDChannel
from feb_manager import FEBManager

manager = FEBManager("/dev/ttyUSB0")

manager.configure_hv(channel_id=0, unit_id=1)
manager.configure_led(channel_id=1, unit_id=2)

hv = manager.channel(0).device
hv.set_voltage(1250.0)

led = manager.channel(1).device
led.set_state(True)
