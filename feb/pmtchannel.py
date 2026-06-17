from feb.devices import DeviceType, DeviceConfig, DeviceChannel
from enum import Enum, IntFlag

class PMTChannel(DeviceChannel):
    DEVICE_TYPE = DeviceType.PMT

    # helpers

    STATUS_MAP = {
        0: "UP",
        1: "DOWN",
        2: "RUP",
        3: "RDN",
        4: "TUP",
        5: "TDN",
        6: "TRIP",
    }

    class Alarm(IntFlag):
        OV = 1
        UV = 2
        OC = 4
        OT = 8

    ALARM_MAP = {
        Alarm.OV: "OV",
        Alarm.UV: "UV",
        Alarm.OC: "OC",
        Alarm.OT: "OT",
    }

    def __init__(self, modbus, channel: int, address: int):
        super().__init__(modbus, channel, address)
        self.probe()

    def probe(self):
        try:
            self.getStatus()
        except Exception as e:
            self.online = False
        else:
            self.online = True

    def alarm_string(self, alarm_code):
        alarms = self.Alarm(alarm_code)

        if alarms == 0:
            return "none"

        return " ".join(name for flag, name in self.ALARM_MAP.items() if alarms & flag)

    @staticmethod
    def convertTemperature(value):
        q = (value & 0xFF) / 1000
        i = (value >> 8) & 0xFF
        return round(q + i, 1)

    @DeviceChannel.track_connection
    def getStatus(self) -> dict:
        rr = self.modbus.read_holding_registers(address=6, count=1, slave=self.address)
        return {"value": rr.registers[0], "string": self.STATUS_MAP.get(rr.registers[0], "undef")}

    @DeviceChannel.track_connection
    def getVoltage(self) -> float:
        rr = self.modbus.read_holding_registers(address=0x2A, count=2, slave=self.address)
        rr.registers.reverse()
        return self.modbus.convert_from_registers(rr.registers, data_type=self.modbus.DATATYPE.INT32) / 1000

    @DeviceChannel.track_connection
    def getVoltageSet(self) -> int:
        rr = self.modbus.read_holding_registers(address=0x26, count=1, slave=self.address)
        return rr.registers[0]

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(25, 1500)
    def setVoltageSet(self, value: int):
        self.modbus.write_register(address=0x26, value=value, slave=self.address)

    @DeviceChannel.track_connection
    def getCurrent(self) -> float:
        rr = self.modbus.read_holding_registers(address=0x28, count=2, slave=self.address)
        rr.registers.reverse()
        return self.modbus.convert_from_registers(rr.registers, data_type=self.modbus.DATATYPE.INT32) / 1000

    @DeviceChannel.track_connection
    def getTemperature(self) -> float:
        rr = self.modbus.read_holding_registers(address=0x7, count=1, slave=self.address)
        return self.convertTemperature(rr.registers[0])

    @DeviceChannel.track_connection
    def getRateRampup(self) -> int:
        rr = self.modbus.read_holding_registers(address=0x23, count=2, slave=self.address)
        return rr.registers[0]   

    @DeviceChannel.track_connection
    def getRateRampdown(self) -> int:
        rr = self.modbus.read_holding_registers(address=0x23, count=2, slave=self.address)
        return rr.registers[1]   

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(1, 25)
    def setRateRampup(self, value: int):
        self.modbus.write_register(address=0x23, value=value, slave=self.address)

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(1, 25)
    def setRateRampdown(self, value: int):
        self.modbus.write_register(address=0x24, value=value, slave=self.address)

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(1, 20)
    def setLimitVoltage(self, value: int):
        self.modbus.write_register(address=0x27, value=value, slave=self.address)

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(1, 10)
    def setLimitCurrent(self, value: int):
        self.modbus.write_register(address=0x25, value=value, slave=self.address)

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(20, 70)
    def setLimitTemperature(self, value: int):
        self.modbus.write_register(address=0x2F, value=value, slave=self.address)

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(1, 1000)
    def setLimitTriptime(self, value: int):
        self.modbus.write_register(address=0x22, value=value, slave=self.address)

    @DeviceChannel.track_connection
    @DeviceChannel.validate_range(0, 2500)
    def setThreshold(self, value: float):
        self.modbus.write_register(address=0x2D, value=math.floor(value), slave=self.address)
        self.modbus.write_register(address=0x35, value=int(value * 10) % 10, slave=self.address)

    @DeviceChannel.track_connection
    def getThreshold(self) -> float:
        ri = self.modbus.read_holding_registers(address=0x2D, count=1, slave=self.address)
        rf = self.modbus.read_holding_registers(address=0x35, count=1, slave=self.address)
        return ri.registers[0] + rf.registers[0]/10

    @DeviceChannel.track_connection
    def getAlarm(self) -> dict:
        rr = self.modbus.read_holding_registers(address=0x2E, count=1, slave=self.address)
        return {"value": rr.registers[0], "string": self.alarm_string(rr.registers[0])}

    @DeviceChannel.track_connection
    def getVref(self) -> float:
        rr = self.modbus.read_holding_registers(address=0x2C, count=1, slave=self.address)
        return rr.registers[0]/10

    @DeviceChannel.track_connection
    def powerOn(self):
        self.modbus.write_coil(address=1, value=True, slave=self.address)

    @DeviceChannel.track_connection
    def powerOff(self):
        self.modbus.write_coil(address=1, value=False, slave=self.address)

    @DeviceChannel.track_connection
    def reset(self):
        self.modbus.write_coil(address=2, value=True, slave=self.address)

    @DeviceChannel.track_connection
    def getInfo(self) -> dict:
        l = self.modbus.read_holding_registers(address=0x02, count=1, slave=self.address).registers
        fwver = struct.pack(f'>{len(l)}h', *l).decode().rstrip('\x00')
        l = self.modbus.read_holding_registers(address=0x08, count=6, slave=self.address).registers
        pmtsn = struct.pack(f'>{len(l)}h', *l).decode().rstrip('\x00')
        l = self.modbus.read_holding_registers(address=0x0E, count=6, slave=self.address).registers
        hvsn = struct.pack(f'>{len(l)}h', *l).decode().rstrip('\x00')
        l = self.modbus.read_holding_registers(address=0x14, count=6, slave=self.address).registers
        febsn = struct.pack(f'>{len(l)}h', *l).decode().rstrip('\x00')
        l = self.modbus.read_holding_registers(address=0x04, count=2, slave=self.address).registers
        devid = (l[1] << 16) + l[0]
        return {"fwver": fwver, "pmtsn": pmtsn, "hvsn": hvsn, "febsn": febsn, "devid": str(devid)}

    @DeviceChannel.track_connection
    def setPMTSerialNumber(self, sn: str):
        data = self.modbus.convert_to_registers(sn.ljust(12, '\0'), self.modbus.DATATYPE.STRING)
        self.modbus.write_registers(address=0x08, values=data,
          slave=self.address, no_response_expected=True)

    @DeviceChannel.track_connection
    def setHVSerialNumber(self, sn: str):
        data = self.modbus.convert_to_registers(sn.ljust(12, '\0'), self.modbus.DATATYPE.STRING)
        self.modbus.write_registers(address=0x0E, values=data,
          slave=self.address, no_response_expected=True)

    @DeviceChannel.track_connection
    def setFEBSerialNumber(self, sn: str):
        data = self.modbus.convert_to_registers(sn.ljust(12, '\0'), self.modbus.DATATYPE.STRING)
        self.modbus.write_registers(address=0x14, values=data,
          slave=self.address, no_response_expected=True)

    @DeviceChannel.validate_range(1, 20)
    def setModbusAddress(self, addr: int):
        self.modbus.write_register(address=0x00, value=addr, slave=self.address)

    @DeviceChannel.track_connection
    def readMonRegisters(self) -> dict:
        monData = {}
        rr = self.modbus.read_holding_registers(address=0, count=54, slave=self.address)

        if rr.isError():
           return {}

        monData['status'] = { 
            "value": rr.registers[0x0006], 
            "string": self.STATUS_MAP.get(rr.registers[0x0006], "undef")
        }
        #monData['status']['value'] = rr.registers[0x0006]
        #monData['status']['string'] = self.STATUS_MAP.get(rr.registers[0x0006], "undef")
        monData['Vset'] = rr.registers[0x0026]
        monData['V'] = ((rr.registers[0x002B] << 16) + rr.registers[0x002A]) / 1000
        monData['I'] = ((rr.registers[0x0029] << 16) + rr.registers[0x0028]) / 1000
        monData['T'] = self.convertTemperature(rr.registers[0x0007])
        monData['rateUP'] = rr.registers[0x0023]
        monData['rateDN'] = rr.registers[0x0024]
        monData['limitV'] = rr.registers[0x0027]
        monData['limitI'] = rr.registers[0x0025]
        monData['limitT'] = rr.registers[0x002F]
        monData['limitTRIP'] = rr.registers[0x0022]
        threshold = rr.registers[0x002D] + (rr.registers[0x0035] / 10)
        monData['threshold'] = rr.registers[0x002D] + rr.registers[0x0035]/10
        monData['alarm'] = {
            "value": rr.registers[0x002E],
            "string": self.alarm_string(rr.registers[0x002E])
        }
        #monData['alarm']['value'] = rr.registers[0x002E]
        #monData['alarm']['string'] = self.alarm_string(rr.registers[0x002E])
        
        return monData

    @DeviceChannel.track_connection
    def readCalibRegisters(self) -> dict:
        rr = self.modbus.read_holding_registers(address=0x30, count=5, slave=self.address)
        mlsb = rr.registers[0]
        mmsb = rr.registers[1]
        qlsb = rr.registers[2]
        qmsb = rr.registers[3]
        calibt = rr.registers[4]

        calibm = ((mmsb << 16) + mlsb)
        calibm = struct.unpack('l', struct.pack('L', calibm & 0xffffffff))[0]
        calibm = calibm / 10000

        calibq = ((qmsb << 16) + qlsb)
        calibq = struct.unpack('l', struct.pack('L', calibq & 0xffffffff))[0]
        calibq = calibq / 10000

        calibt = round(calibt / 1.6890722, 2)

        return {"slope": calibm, "offset": calibq, "discr": calibt}

    @DeviceChannel.track_connection
    def writeCalibSlope(self, slope: float):
        slope = int(slope * 10000)
        lsb = (slope & 0xFFFF)
        msb = (slope >> 16) & 0xFFFF
        self.modbus.write_registers(address=0x30, values=[lsb, msb], slave=self.address, no_response_expected=True)

    @DeviceChannel.track_connection
    def writeCalibOffset(self, offset: float):
        offset = int(offset * 10000)
        lsb = (offset & 0xFFFF)
        msb = (offset >> 16) & 0xFFFF
        self.modbus.write_registers(address=0x32, values=[lsb, msb], slave=self.address, no_response_expected=True)

    @DeviceChannel.track_connection
    def writeCalibDiscr(self, discr: float):
        discr = int(discr * 1.6890722)
        self.modbus.write_register(address=0x34, value=discr, slave=self.address)

