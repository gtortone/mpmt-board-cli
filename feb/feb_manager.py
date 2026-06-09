
from devices import HVChannel, LEDChannel
from feb_channel import FEBChannel
from modbus_manager import ModbusManager, ModbusConfig

class FEBManager:
    def __init__(self, cfg: ModbusConfig):
        self.modbus = ModbusManager(cfg)
        #self.modbus.connect()

        self._channels = [
            FEBChannel(i)
            for i in range(cfg.max_slave)
        ]

    def channel(self, i: int) -> FEBChannel: 
        if not 0 <= i < len(self._channels):
            raise IndexError(f"Invalid channel index {i}")

        return self._channels[i]

    def configure_hv(self, channel_id: int, unit_id: int):
        device = HVChannel(self.modbus, unit_id, channel_id)
        self.channel(channel_id).attach(device)

    def configure_led(self, channel_id: int, unit_id: int):
        device = LEDChannel(self.modbus, unit_id, channel_id)
        self.channel(channel_id).attach(device)
