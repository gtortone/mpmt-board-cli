
from abc import ABC

class DeviceChannel(ABC):
    def __init__(self, modbus, unit_id: int, channel_id: int):
        self.modbus = modbus
        self.unit_id = unit_id
        self.channel_id = channel_id

class HVChannel(DeviceChannel):
    def set_voltage(self, voltage: float):
        addr = 100 + self.channel_id
        value = int(voltage * 10)
        self.modbus.write_register(self.unit_id, addr, value)


class LEDChannel(DeviceChannel):
    def set_state(self, state: bool):
        addr = 200 + self.channel_id
        value = 1 if state else 0
        self.modbus.write_register(self.unit_id, addr, value)
