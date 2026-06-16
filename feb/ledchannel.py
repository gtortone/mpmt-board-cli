from feb.devices import DeviceType, DeviceConfig, DeviceChannel

class LEDChannel(DeviceChannel):
    DEVICE_TYPE = DeviceType.LED

    def __init__(self, modbus, channel: int, address: int):
        super().__init__(modbus, channel, address)
        # probe device
        try:
            self.getInfo()
        except Exception as e:
            self.online = False
        else:
            self.online = True

    @DeviceChannel.track_connection
    def getInfo(self) -> dict:
        rr = self.modbus.read_input_registers(address=30001, count=1, slave=self.address).registers
        fwver = f"{rr[0] >> 8}.{(rr[0] & 0xF0) >> 4}.{rr[0] & 0x0F}"
        return {"fwver": fwver}

    @DeviceChannel.validate_range(20, 40)
    def setModbusAddress(self, addr: int):
        self.modbus.write_register(address=0x40006, value=addr, slave=self.address)
