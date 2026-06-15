from feb.devices import DeviceType, DeviceConfig, DeviceChannel

class LEDChannel(DeviceChannel):
    DEVICE_TYPE = DeviceType.LED

    @DeviceChannel.validate_range(1, 20)
    def setModbusAddress(self, addr: int):
        self.modbus.write_register(address=0x00, value=addr, slave=self.address)
