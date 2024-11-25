import minimalmodbus
import struct
from enum import Enum
from pyModbusTCP.client import ModbusClient
from sys import exit

class HVModbus:
   def __init__(self, param):
      self.devset = [None] * 21     # 1...20 for new boards default address (20)
      self.dev = None
      self.client = None
      self.address = None
      self.param = param

      # in TCP mode try to connect to mbusd
      if self.param.mode == 'tcp':
         self.client = ModbusClient(host=self.param.host, port=502, auto_open=True, timeout=5)
         if self.client.open() is False:
            print(f'E: host not reachable or mbusd not running ({self.param.host})')
            exit(1) 

   def open(self, addr):
      if self.param.mode == 'rtu':
         if (self.probe(addr)):
            self.dev = minimalmodbus.Instrument(self.param.port, addr)
            self.dev.serial.baudrate = 115200
            # timeout increased for write operations
            self.dev.serial.timeout = 0.5
            self.dev.mode = minimalmodbus.MODE_RTU
            #self.dev.debug = True
            self.address = addr
            return True
         else:
            return False
      elif self.param.mode == 'tcp':
         if(self.probeTCP(addr)):
            return True

   def probe(self, addr):
      if self.param.mode == 'rtu':
         return self.probeRTU(addr)
      elif self.param.mode == 'tcp':
         return self.probeTCP(addr)

   def probeRTU(self, addr, timeout=0.1):
      dev =  minimalmodbus.Instrument(self.param.port, addr)
      dev.serial.baudrate = 115200
      # low timeout to do fast probing
      dev.serial.timeout = timeout
      dev.mode = minimalmodbus.MODE_RTU

      found = False
      for _ in range(0,3):
         try:
            dev.read_register(0x00)  # read modbus address register
         except IOError:
            dev.serial.timeout += 0.1
         else:
            self.devset[addr] = dev
            # timeout increased for write operations
            self.devset[addr].serial.timeout = 0.5
            found = True
            break;

      return found

   def probeTCP(self, addr):
      c = ModbusClient(host=self.param.host, port=502, unit_id=addr, auto_open=True, timeout=5)
      reg = c.read_holding_registers(0x00)
      if reg is None:
         return False
      else:
         self.address = addr
         return True

   def isConnected(self):
      return (self.address is not None)

   def getAddress(self):
      return self.address

   def getStatus(self, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         return d.read_register(0x0006)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         return self.client.read_holding_registers(0x0006)[0]

   def getVoltage(self, devnum=None):
      lsb = msb = 0
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         lsb = d.read_register(0x002A)
         msb = d.read_register(0x002B)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         lsb = self.client.read_holding_registers(0x002A)[0]
         msb = self.client.read_holding_registers(0x002B)[0]
      value = (msb << 16) + lsb
      return (value / 1000)

   def getVoltageSet(self, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         return d.read_register(0x0026)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         return self.client.read_holding_registers(0x0026)[0]

   def setVoltageSet(self, value, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0026, value)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0026, value) 

   def getCurrent(self, devnum=None):
      lsb = msb = 0
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         lsb = d.read_register(0x0028)
         msb = d.read_register(0x0029)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         lsb = self.client.read_holding_registers(0x0028)[0]
         msb = self.client.read_holding_registers(0x0029)[0]
      value = (msb << 16) + lsb
      return (value / 1000)

   def convertTemperature(self, value):
      q = (value & 0xFF) / 1000
      i = (value >> 8) & 0xFF
      return round(q+i, 1)

   def getTemperature(self, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         value = d.read_register(0x0007)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         value = self.client.read_holding_registers(0x0007)[0]

      return self.convertTemperature(value)

   def getRate(self, fmt=str, devnum=None):
      rup = rdn = 0
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         rup = d.read_register(0x0023)
         rdn = d.read_register(0x0024)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         rup = self.client.read_holding_registers(0x0023)[0]
         rdn = self.client.read_holding_registers(0x0024)[0]
      if (fmt == str):
         return f'{rup}/{rdn}' 
      else:
         return (rup, rdn)

   def setRateRampup(self, value, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0023, value, functioncode=6)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0023, value) 

   def setRateRampdown(self, value, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0024, value)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0024, value)

   def getLimit(self, fmt=str, devnum=None):
      lv = li = lt = ltt = 0
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         lv = d.read_register(0x0027)
         li = d.read_register(0x0025)
         lt = d.read_register(0x002F)
         ltt = d.read_register(0x0022)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         lv = self.client.read_holding_registers(0x0027)[0]
         li = self.client.read_holding_registers(0x0025)[0]
         lt = self.client.read_holding_registers(0x002F)[0]
         ltt = self.client.read_holding_registers(0x0022)[0]
      if (fmt == str):
         return f'{lv}/{li}/{lt}/{ltt}'
      else:
         return (lv, li, lt, ltt)

   def setLimitVoltage(self, value, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0027, value)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0027, value)

   def setLimitCurrent(self, value, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0025, value)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0025, value)

   def setLimitTemperature(self, value, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x002F, value)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x002F, value)

   def setLimitTriptime(self, value, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0022, value)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0022, value)

   def setThreshold(self, value, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x002D, value)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x002D, value)

   def getThreshold(self, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         return d.read_register(0x002D)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         return self.client.read_holding_registers(0x002D)[0]

   def getAlarm(self, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         return d.read_register(0x002E)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         return self.client.read_holding_registers(0x002E)[0]

   def getVref(self, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         return d.read_register(0x002C)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         return self.client.read_holding_registers(0x002C)[0]

   def powerOn(self, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_bit(1, True)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_coil(1, True)

   def powerOff(self, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_bit(1, False)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_coil(1, False)

   def reset(self, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_bit(2, True)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_coil(2, True)

   def getInfo(self, devnum=None):
      fwver = pmtsn = hvsn = febsn = ""
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         fwver = d.read_string(0x0002, 1)
         pmtsn = d.read_string(0x0008, 6)
         hvsn = d.read_string(0x000E, 6)
         febsn = d.read_string(0x0014, 6)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         l = self.client.read_holding_registers(0x0002, 1)
         fwver = struct.pack(f'>{len(l)}h', *l).decode()
         l = self.client.read_holding_registers(0x0008, 6)
         pmtsn = struct.pack(f'>{len(l)}h', *l).decode()
         l = self.client.read_holding_registers(0x000E, 6)
         hvsn = struct.pack(f'>{len(l)}h', *l).decode()
         l = self.client.read_holding_registers(0x0014, 6)
         febsn = struct.pack(f'>{len(l)}h', *l).decode()
         
      return (fwver, pmtsn, hvsn, febsn)

   def setPMTSerialNumber(self, sn, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_string(0x0008, sn, 6)
      elif self.param.mode == 'tcp':
         l = list(bytes(sn.ljust(12), 'utf-8'))
         data = struct.pack(f'>{len(l)}h', *l)
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_multiple_registers(0x0008, data)

   def setHVSerialNumber(self, sn, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_string(0x000E, sn, 6)
      elif self.param.mode == 'tcp':
         l = list(bytes(sn.ljust(12), 'utf-8'))
         data = struct.pack(f'>{len(l)}h', *l)
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_multiple_registers(0x000E, data)

   def setFEBSerialNumber(self, sn, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_string(0x0014, sn, 6)
      elif self.param.mode == 'tcp':
         l = list(bytes(sn.ljust(12), 'utf-8'))
         data = struct.pack(f'>{len(l)}h', *l)
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_multiple_registers(0x0014, data)
      
   def setModbusAddress(self, addr, devnum=None):
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0000, addr)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0000, addr)

   def readMonRegisters(self, devnum=None):
      regs = []
      monData = {}
      baseAddress = 0x0000
      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         regs = d.read_registers(baseAddress, 48)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         regs = self.client.read_holding_registers(baseAddress, 48)

      if regs is None:
         return None

      monData['status'] = regs[0x0006]
      monData['Vset'] = regs[0x0026]
      monData['V'] = ((regs[0x002B] << 16) + regs[0x002A]) / 1000
      monData['I'] = ((regs[0x0029] << 16) + regs[0x0028]) / 1000
      monData['T'] = self.convertTemperature(regs[0x0007])
      monData['rateUP'] = regs[0x0023]
      monData['rateDN'] = regs[0x0024]
      monData['limitV'] = regs[0x0027]
      monData['limitI'] = regs[0x0025]
      monData['limitT'] = regs[0x002F]
      monData['limitTRIP'] = regs[0x0022]
      monData['threshold'] = regs[0x002D]
      monData['alarm'] = regs[0x002E]
      
      return monData

   def readCalibRegisters(self, devnum=None):
      mlsb = mmsb = qlsb = qmsb = calibt = 0
      if self.param.mode == 'rtu': 
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         mlsb = d.read_register(0x0030)
         mmsb = d.read_register(0x0031)
         qlsb = d.read_register(0x0032)
         qmsb = d.read_register(0x0033)
         calibt = d.read_register(0x0034)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         mlsb = self.client.read_holding_registers(0x0030)[0]
         mmlsb = self.client.read_holding_registers(0x0031)[0]
         qlsb = self.client.read_holding_registers(0x0032)[0]
         qmsb = self.client.read_holding_registers(0x0033)[0]
         calibt = self.client.read_holding_registers(0x0034)[0]

      calibm = ((mmsb << 16) + mlsb)
      calibm = struct.unpack('l', struct.pack('L', calibm & 0xffffffff))[0]
      calibm = calibm / 10000

      calibq = ((qmsb << 16) + qlsb)
      calibq = struct.unpack('l', struct.pack('L', calibq & 0xffffffff))[0]
      calibq = calibq / 10000

      calibt = calibt / 1.6890722

      return (calibm, calibq, calibt)

   def writeCalibSlope(self, slope, devnum=None):
      slope = int(slope * 10000)
      lsb = (slope & 0xFFFF)
      msb = (slope >> 16) & 0xFFFF

      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0030, lsb)
         d.write_register(0x0031, msb)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0030, lsb)
         self.client.write_single_register(0x0031, msb)

   def writeCalibOffset(self, offset, devnum=None):
      offset = int(offset * 10000)
      lsb = (offset & 0xFFFF)
      msb = (offset >> 16) & 0xFFFF

      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0032, lsb)
         d.write_register(0x0033, msb)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0032, lsb)
         self.client.write_single_register(0x0033, msb)
   
   def writeCalibDiscr(self, discr, devnum=None):
      discr = int(discr * 1.6890722)

      if self.param.mode == 'rtu':
         if devnum: d = self.devset[devnum]
         else: d = self.dev
         d.write_register(0x0034, discr)
      elif self.param.mode == 'tcp':
         if devnum is not None:
            self.client.unit_id = devnum
         else:
            self.client.unit_id = self.address
         self.client.write_single_register(0x0034, discr)
