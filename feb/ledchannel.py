from feb.devices import DeviceType, DeviceConfig, DeviceChannel
from runcontrol.fpga import FPGA
from enum import Enum

class LEDChannel(DeviceChannel):
    DEVICE_TYPE = DeviceType.LED

    # helpers
    
    # used for coils
    STATUS_MAP = {
        0: "OFF",
        1: "ON",
    }

    class TriggerSource(Enum):
        MAINBOARD = 0,
        MCU = 1,
        EXT = 2

    REG_LED_BASE = 85

    def __init__(self, modbus, channel: int, address: int):
        super().__init__(modbus, channel, address)
        self.fpga = FPGA('/dev/uio0')
        self.probe()

    def probe(self):
        try:
            self.getInfo()
        except Exception as e:
            self.online = False
        else:
            self.online = True

    @DeviceChannel.track_connection
    def powerOn(self):
        rr = self.modbus.write_coil(address=1, value=True, slave=self.address)
        return not rr.isError()

    @DeviceChannel.track_connection
    def powerOff(self):
        rr = self.modbus.write_coil(address=1, value=False, slave=self.address)
        return not rr.isError()

    @DeviceChannel.track_connection
    def getStatus(self) -> dict:
        rr = self.modbus.read_discrete_inputs(address=10001, count=1, slave=self.address)
        # add Trigger, Bias...
        return {"value": int(rr.bits[0]), "string": self.STATUS_MAP.get(rr.bits[0], "undef")}

    @DeviceChannel.track_connection
    def getInfo(self) -> dict:
        rr = self.modbus.read_input_registers(address=30001, count=1, slave=self.address).registers
        fwver = f"{rr[0] >> 8}.{(rr[0] & 0xF0) >> 4}.{rr[0] & 0x0F}"
        return {"fwver": fwver}

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(0, 1)
    def setTrigger(self, value: int):
        rr = self.modbus.write_coil(address=2, value=bool(value), slave=self.address)
        return not rr.isError()

    @DeviceChannel.track_connection
    def getTriggerStatus(self):
        rr = self.modbus.read_coils(address=2, count=1, slave=self.address)
        return {"value": int(rr.bits[0]), "string": self.STATUS_MAP.get(rr.bits[0], "undef")}

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(0, 1)
    def setBias(self, value: int):
        rr = self.modbus.write_coil(address=3, value=bool(value), slave=self.address)
        return not rr.isError()

    @DeviceChannel.track_connection
    def getBiasStatus(self):
        rr = self.modbus.read_coils(address=3, count=1, slave=self.address)
        return {"value": int(rr.bits[0]), "string": self.STATUS_MAP.get(rr.bits[0], "undef")}

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(2.02, 15.28)
    def setBiasVoltage(self, value: float):
        dac_level = int(4711.9 - 307.97 * value)
        if dac_level > 4095:
            dac_level = 4095
        elif dac_level < 0:
            dac_level = 0
        rr = self.modbus.write_register(address=40003, value=dac_level, slave=self.address)     
        if not rr.isError():
            # update FPGA register
            regval = self.fpga.readRegister(self.REG_LED_BASE + self.channel) & 0x7F000
            regval |= (dac_level & 0xFFF)
            self.fpga.writeRegister(self.REG_LED_BASE + self.channel, regval)

    @DeviceChannel.track_connection
    def getBiasVoltage(self) -> float:
        adc_level = self.modbus.read_holding_registers(address=40004, 
            count=1, slave=self.address).registers[0] & 0xFFF;
        level_in_volts = adc_level / 248.242
        return round(level_in_volts, 2)

    @DeviceChannel.track_connection
    #@DeviceChannel.validate_range(1, 7)
    def setChannel(self, value: int):
        rr = self.modbus.write_register(address=40002, value=value, slave=self.address)     
        if not rr.isError():
            # update FPGA register
            regval = self.fpga.readRegister(self.REG_LED_BASE + self.channel) & 0xFFF
            regval |= (value & 0x7F) << 12
            self.fpga.writeRegister(self.REG_LED_BASE + self.channel, regval)

    @DeviceChannel.track_connection
    def setTriggerSource(self, source: TriggerSource):
        rr = self.modbus.write_register(address=40001, value=source, slave=self.address)

    @DeviceChannel.track_connection
    def getCurrent(self):
        adc_level = self.modbus.read_holding_registers(address=40005,
            count=1, slave=self.address).registers[0] & 0xFFF; 
        level_in_ma = adc_level / 248.242
        return round(level_in_ma, 2)
    
    @DeviceChannel.validate_range(20, 40)
    def setModbusAddress(self, addr: int):
        self.modbus.write_register(address=0x40006, value=addr, slave=self.address)

