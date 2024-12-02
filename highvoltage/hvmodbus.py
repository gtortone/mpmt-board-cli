import struct
from enum import Enum
from sys import exit

import pymodbus.client as ModbusClient
from pymodbus.utilities import ModbusTransactionState
from pymodbus import (
    FramerType,
    ModbusException,
    pymodbus_apply_logging_config,
)

class HVModbus:
   def __init__(self, param):
      self.devset = [None] * 21     # 1...20 for new boards default address (20)
      self.dev = None
      self.client = None
      self.address = None
      self.param = param

      if self.param.mode == 'tcp':
         self.client = ModbusClient.ModbusTcpClient(self.param.host, port=502, framer=FramerType.SOCKET)
         if self.client.connect() == False:
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
            timeout=0.5
         )
         if self.client.connect() == False:
            print(f'E: port not available ({self.param.port})')
            exit(1) 

   def open(self, addr):
      rr = None

      self.handleInterruptedRequest()

      try:
         rr = self.client.read_holding_registers(address=0, count=1, slave=addr)
      except ModbusException as e:
         print(e)
         return False

      if rr.isError():
         return False

      self.address = addr
      return True

   def handleInterruptedRequest(self):
      if self.client.state != ModbusTransactionState.TRANSACTION_COMPLETE:
         self.client.close()
      
   def isConnected(self):
      return (self.address is not None)

   def getAddress(self):
      return self.address

   def getStatus(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=6, count=1, slave=slave)
      return rr.registers[0]

   def getVoltage(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0x2A, count=2, slave=slave)
      rr.registers.reverse()
      return (self.client.convert_from_registers(rr.registers, data_type=self.client.DATATYPE.INT32) / 1000)

   def getVoltageSet(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0x26, count=1, slave=slave)
      return rr.registers[0]

   def setVoltageSet(self, value, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      self.client.write_register(address=0x26, value=value, slave=slave)

   def getCurrent(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0x28, count=2, slave=slave)
      rr.registers.reverse()
      return (self.client.convert_from_registers(rr.registers, data_type=self.client.DATATYPE.INT32) / 1000)

   def convertTemperature(self, value):
      q = (value & 0xFF) / 1000
      i = (value >> 8) & 0xFF
      return round(q+i, 1)

   def getTemperature(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0x7, count=1, slave=slave)
      return self.convertTemperature(rr.registers[0])

   def getRate(self, fmt=str, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0x23, count=2, slave=slave)
      rup = rr.registers[0]
      rdn = rr.registers[1]
      if (fmt == str):
         return f'{rup}/{rdn}' 
      else:
         return (rup, rdn)

   def setRateRampup(self, value, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      self.client.write_register(address=0x23, value=value, slave=slave)

   def setRateRampdown(self, value, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      self.client.write_register(address=0x24, value=value, slave=slave)

   def getLimit(self, fmt=str, slave=None):
      slave = self.address if slave == None else slave

      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0, count=48, slave=slave)
      lv = rr.registers[0x27]
      li = rr.registers[0x25]
      lt = rr.registers[0x2F]
      ltt = rr.registers[0x22]

      if (fmt == str):
         return f'{lv}/{li}/{lt}/{ltt}'
      else:
         return (lv, li, lt, ltt)

   def setLimitVoltage(self, value, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      self.client.write_register(address=0x27, value=value, slave=slave)

   def setLimitCurrent(self, value, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      self.client.write_register(address=0x25, value=value, slave=slave)

   def setLimitTemperature(self, value, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      self.client.write_register(address=0x2F, value=value, slave=slave)

   def setLimitTriptime(self, value, slave=None):
      slave = self.address if slave == None else slave
      self.client.write_register(address=0x22, value=value, slave=slave)

   def setThreshold(self, value, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      self.client.write_register(address=0x2D, value=value, slave=slave)

   def getThreshold(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0x2D, count=1, slave=slave)
      return rr.registers[0]

   def getAlarm(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0x2E, count=1, slave=slave)
      return rr.registers[0]

   def getVref(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0x2C, count=1, slave=slave)
      return rr.registers[0]

   def powerOn(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.write_coil(address=1, value=True, slave=slave)
      return (not rr.isError())

   def powerOff(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.write_coil(address=1, value=False, slave=slave)
      return (not rr.isError())

   def reset(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.write_coil(address=2, value=True, slave=slave)
      return (not rr.isError())

   def getInfo(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      l = self.client.read_holding_registers(address=0x02, count=1, slave=slave).registers
      fwver = struct.pack(f'>{len(l)}h', *l).decode()
      l = self.client.read_holding_registers(address=0x08, count=6, slave=slave).registers
      pmtsn = struct.pack(f'>{len(l)}h', *l).decode()
      l = self.client.read_holding_registers(address=0x0E, count=6, slave=slave).registers
      hvsn = struct.pack(f'>{len(l)}h', *l).decode()
      l = self.client.read_holding_registers(address=0x14, count=6, slave=slave).registers
      febsn = struct.pack(f'>{len(l)}h', *l).decode()
      return (fwver, pmtsn, hvsn, febsn)

   def setPMTSerialNumber(self, sn, slave=None):
      slave = self.address if slave == None else slave
      data = list(bytes(sn.ljust(12), 'utf-8'))
      self.handleInterruptedRequest()
      self.client.write_registers(address=0x08, values=data, slave=slave)

   def setHVSerialNumber(self, sn, slave=None):
      slave = self.address if slave == None else slave
      data = list(bytes(sn.ljust(12), 'utf-8'))
      self.handleInterruptedRequest()
      self.client.write_registers(address=0x0E, values=data, slave=slave)

   def setFEBSerialNumber(self, sn, slave=None):
      slave = self.address if slave == None else slave
      data = list(bytes(sn.ljust(12), 'utf-8'))
      self.handleInterruptedRequest()
      self.client.write_registers(address=0x14, values=data, slave=slave)

   def setModbusAddress(self, addr, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      self.client.write_register(address=0x00, value=addr, slave=slave)

   def readMonRegisters(self, slave=None):
      slave = self.address if slave == None else slave

      monData = {}
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0, count=48, slave=slave)

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
      monData['threshold'] = rr.registers[0x002D]
      monData['alarm'] = rr.registers[0x002E]
      
      return monData

   def readCalibRegisters(self, slave=None):
      slave = self.address if slave == None else slave
      self.handleInterruptedRequest()
      rr = self.client.read_holding_registers(address=0x30, count=5, slave=slave)
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

      return (calibm, calibq, calibt)

   def writeCalibSlope(self, slope, slave=None):
      slave = self.address if slave == None else slave
      slope = int(slope * 10000)
      lsb = (slope & 0xFFFF)
      msb = (slope >> 16) & 0xFFFF

      self.handleInterruptedRequest()
      self.client.write_registers(address=0x30, values=[lsb, msb], slave=slave)

   def writeCalibOffset(self, offset, slave=None):
      slave = self.address if slave == None else slave
      offset = int(offset * 10000)
      lsb = (offset & 0xFFFF)
      msb = (offset >> 16) & 0xFFFF

      self.handleInterruptedRequest()
      self.client.write_registers(address=0x32, values=[lsb, msb], slave=slave)

   def writeCalibDiscr(self, discr, slave=None):
      slave = self.address if slave == None else slave
      discr = int(discr * 1.6890722)

      self.handleInterruptedRequest()
      self.client.write_register(address=0x34, value=discr, slave=slave)
