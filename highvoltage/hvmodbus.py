import struct
import math
from sys import exit
from mini_rpc import rpc_service, rpc_method

import pymodbus.client as ModbusClient
from pymodbus import (
    FramerType,
    ModbusException,
)

@rpc_service()
class HVModbus:
   def __init__(self, param):
      self.devset = [None] * 21     # 1...20 for new boards default address (20)
      self.dev = None
      self.client = None
      self.address = None
      self.param = param

      if self.param.mode == 'tcp':
         self.client = ModbusClient.ModbusTcpClient(self.param.host, port=502, framer=FramerType.SOCKET)
         if not self.client.connect():
            print(f'E: host not reachable or mbusd not running ({self.param.host})')
            exit(1) 
      elif self.param.mode == 'rtu':
         self.client = ModbusClient.ModbusSerialClient(
            self.param.port, 
            framer=FramerType.RTU, 
            baudrate=115200,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=0.1
         )
         if not self.client.connect():
            print(f'E: port not available ({self.param.port})')
            exit(1) 

   @rpc_method
   def open(self, addr) -> int:
      try:
         rr = self.client.read_holding_registers(address=0, count=1, device_id=addr)
      except ModbusException as e:
         #print(e)
         return False

      if rr.isError():
         return False

      return True
      
   @rpc_method
   def getStatus(self, slave) -> int:
      rr = self.client.read_holding_registers(address=6, count=1, device_id=slave)
      return rr.registers[0]

   @rpc_method 
   def getVoltage(self, slave) -> float:
      rr = self.client.read_holding_registers(address=0x2A, count=2, device_id=slave)
      rr.registers.reverse()
      return self.client.convert_from_registers(rr.registers, data_type=self.client.DATATYPE.INT32) / 1000

   @rpc_method
   def getVoltageSet(self, slave) -> int:
      rr = self.client.read_holding_registers(address=0x26, count=1, device_id=slave)
      return rr.registers[0]

   @rpc_method
   def setVoltageSet(self, value: float, slave):
      self.client.write_register(address=0x26, value=value, device_id=slave)

   @rpc_method
   def getCurrent(self, slave) -> float:
      rr = self.client.read_holding_registers(address=0x28, count=2, device_id=slave)
      rr.registers.reverse()
      return self.client.convert_from_registers(rr.registers, data_type=self.client.DATATYPE.INT32) / 1000

   @rpc_method
   def getTemperature(self, slave) -> float:
      rr = self.client.read_holding_registers(address=0x7, count=1, device_id=slave)
      return self.convertTemperature(rr.registers[0])

   @rpc_method
   def getRateRampup(self,  slave) -> int:
      rr = self.client.read_holding_registers(address=0x23, count=2, device_id=slave)
      return rr.registers[0]   

   @rpc_method
   def getRateRampdown(self,  slave) -> int:
      rr = self.client.read_holding_registers(address=0x23, count=2, device_id=slave)
      return rr.registers[1]   

   #def getRate(self, fmt=str, slave) -> str:
   #   rr = self.client.read_holding_registers(address=0x23, count=2, device_id=slave)
   #   rup = rr.registers[0]
   #   rdn = rr.registers[1]
   #   if fmt == str:
   #      return f'{rup}/{rdn}' 
   #   else:
   #      return rup, rdn

   @rpc_method
   def setRateRampup(self, value, slave):
      self.client.write_register(address=0x23, value=value, device_id=slave)

   @rpc_method
   def setRateRampdown(self, value, slave):
      self.client.write_register(address=0x24, value=value, device_id=slave)

   #def getLimit(self, fmt=str, slave) -> float:
   #   rr = self.client.read_holding_registers(address=0, count=48, device_id=slave)
   #   lv = rr.registers[0x27]
   #   li = rr.registers[0x25]
   #   lt = rr.registers[0x2F]
   #   ltt = rr.registers[0x22]

   #   if fmt == str:
   #      return f'{lv}/{li}/{lt}/{ltt}'
   #   else:
   #      return lv, li, lt, ltt

   @rpc_method
   def setLimitVoltage(self, value, slave):
      self.client.write_register(address=0x27, value=value, device_id=slave)

   @rpc_method
   def setLimitCurrent(self, value, slave):
      self.client.write_register(address=0x25, value=value, device_id=slave)

   @rpc_method
   def setLimitTemperature(self, value, slave):
      self.client.write_register(address=0x2F, value=value, device_id=slave)

   @rpc_method
   def setLimitTriptime(self, value, slave):
      self.client.write_register(address=0x22, value=value, device_id=slave)

   @rpc_method
   def setThreshold(self, value, slave):
      self.client.write_register(address=0x2D, value=math.floor(value), device_id=slave)
      self.client.write_register(address=0x35, value=int(value * 10) % 10, device_id=slave)

   @rpc_method
   def getThreshold(self, slave) -> float:
      print("getThreshold")
      ri = self.client.read_holding_registers(address=0x2D, count=1, device_id=slave)
      rf = self.client.read_holding_registers(address=0x35, count=1, device_id=slave)
      return ri.registers[0] + rf.registers[0]/10

   @rpc_method
   def getAlarm(self, slave) -> int:
      rr = self.client.read_holding_registers(address=0x2E, count=1, device_id=slave)
      return rr.registers[0]

   @rpc_method
   def getVref(self, slave) -> float:
      rr = self.client.read_holding_registers(address=0x2C, count=1, device_id=slave)
      return rr.registers[0]/10

   @rpc_method
   def powerOn(self, slave):
      rr = self.client.write_coil(address=1, value=True, device_id=slave)
      return not rr.isError()

   @rpc_method
   def powerOff(self, slave):
      rr = self.client.write_coil(address=1, value=False, device_id=slave)
      return not rr.isError()

   @rpc_method
   def reset(self, slave):
      rr = self.client.write_coil(address=2, value=True, device_id=slave)
      return not rr.isError()

   @rpc_method
   def getInfo(self, slave):
      l = self.client.read_holding_registers(address=0x02, count=1, device_id=slave).registers
      fwver = struct.pack(f'>{len(l)}h', *l).decode()
      l = self.client.read_holding_registers(address=0x08, count=6, device_id=slave).registers
      pmtsn = struct.pack(f'>{len(l)}h', *l).decode()
      l = self.client.read_holding_registers(address=0x0E, count=6, device_id=slave).registers
      hvsn = struct.pack(f'>{len(l)}h', *l).decode()
      l = self.client.read_holding_registers(address=0x14, count=6, device_id=slave).registers
      febsn = struct.pack(f'>{len(l)}h', *l).decode()
      l = self.client.read_holding_registers(address=0x04, count=2, device_id=slave).registers
      devid = (l[1] << 16) + l[0]
      return fwver, pmtsn, hvsn, febsn, devid

   @rpc_method
   def setPMTSerialNumber(self, sn: str, slave):
      data = self.client.convert_to_registers(sn.ljust(12, '\0'), self.client.DATATYPE.STRING)
      self.client.write_registers(address=0x08, values=data,
        device_id=slave, no_response_expected=True)

   @rpc_method
   def setHVSerialNumber(self, sn: str, slave):
      data = self.client.convert_to_registers(sn.ljust(12, '\0'), self.client.DATATYPE.STRING)
      self.client.write_registers(address=0x0E, values=data,
        device_id=slave, no_response_expected=True)

   @rpc_method
   def setFEBSerialNumber(self, sn: str, slave):
      data = self.client.convert_to_registers(sn.ljust(12, '\0'), self.client.DATATYPE.STRING)
      self.client.write_registers(address=0x14, values=data,
        device_id=slave, no_response_expected=True)

   @rpc_method
   def setModbusAddress(self, addr):
      self.client.write_register(address=0x00, value=addr, device_id=slave)

   @rpc_method
   def readMonRegisters(self, slave):
      monData = {}
      rr = self.client.read_holding_registers(address=0, count=54, device_id=slave)

      if rr.isError():
         return None

      monData['status'] = rr.registers[0x0006]
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
      monData['alarm'] = rr.registers[0x002E]
      
      return monData

   @staticmethod
   def convertTemperature(value):
       q = (value & 0xFF) / 1000
       i = (value >> 8) & 0xFF
       return round(q + i, 1)

   @rpc_method
   def readCalibRegisters(self, slave):
      rr = self.client.read_holding_registers(address=0x30, count=5, device_id=slave)
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

      calibt = calibt / 1.6890722

      return calibm, calibq, calibt

   @rpc_method
   def writeCalibSlope(self, slope: float, slave):
      slope = int(slope * 10000)
      lsb = (slope & 0xFFFF)
      msb = (slope >> 16) & 0xFFFF
      self.client.write_registers(address=0x30, values=[lsb, msb], device_id=slave, no_response_expected=True)

   @rpc_method
   def writeCalibOffset(self, offset: float, slave):
      offset = int(offset * 10000)
      lsb = (offset & 0xFFFF)
      msb = (offset >> 16) & 0xFFFF
      self.client.write_registers(address=0x32, values=[lsb, msb], device_id=slave, no_response_expected=True)

   @rpc_method
   def writeCalibDiscr(self, discr: float, slave):
      discr = int(discr * 1.6890722)
      self.client.write_register(address=0x34, value=discr, device_id=slave, no_response_expected=True)
