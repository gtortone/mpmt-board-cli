import minimalmodbus
import struct

class HVModbus:
   def __init__(self):
      self.devset = [None] * 20
      self.dev = None
      self.address = None

   def open(self, serial, addr):
      if (self.probe(serial, addr)):
         self.dev = minimalmodbus.Instrument(serial, addr)
         self.dev.serial.baudrate = 115200
         # timeout increased for write operations
         self.dev.serial.timeout = 0.5
         self.dev.mode = minimalmodbus.MODE_RTU
         #self.dev.debug = True
         self.address = addr
         return True
      else:
         return False

   def probe(self, serial, addr):
      dev =  minimalmodbus.Instrument(serial, addr)
      dev.serial.baudrate = 115200
      # low timeout to do fast probing
      dev.serial.timeout = 0.25
      dev.mode = minimalmodbus.MODE_RTU

      found = False
      for _ in range(0,3):
         try:
            dev.read_register(0x00)  # read modbus address register
         except IOError:
            None
         else:
            self.devset[addr] = dev
            # timeout increased for write operations
            self.devset[addr].serial.timeout = 0.5
            found = True
            break;

      return found

   def isConnected(self):
      return (self.address is not None)

   def getAddress(self):
      return self.address

   def getStatus(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      return d.read_register(0x0006)

   def getVoltage(self, denum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      lsb = d.read_register(0x002A)
      msb = d.read_register(0x002B)
      value = (msb << 16) + lsb
      return (value / 1000)

   def getVoltageSet(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      return d.read_register(0x0026)

   def setVoltageSet(self, value, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_register(0x0026, value)

   def getCurrent(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      lsb = d.read_register(0x0028)
      msb = d.read_register(0x0029)
      value = (msb << 16) + lsb
      return (value / 1000)

   def getTemperature(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      return d.read_register(0x0007)

   def getRate(self, fmt=str, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      rup = d.read_register(0x0023)
      rdn = d.read_register(0x0024)
      if (fmt == str):
         return f'{rup}/{rdn}' 
      else:
         return (rup, rdn)

   def setRateRampup(self, value, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_register(0x0023, value, functioncode=6)

   def setRateRampdown(self, value, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_register(0x0024, value)

   def getLimit(self, fmt=str, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      lv = d.read_register(0x0027)
      li = d.read_register(0x0025)
      lt = d.read_register(0x002F)
      ltt = d.read_register(0x0022)
      if (fmt == str):
         return f'{lv}/{li}/{lt}/{ltt}'
      else:
         return (lv, li, lt, ltt)

   def setLimitVoltage(self, value, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_register(0x0027, value)

   def setLimitCurrent(self, value, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_register(0x0025, value)

   def setLimitTemperature(self, value, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_register(0x002F, value)

   def setLimitTriptime(self, value, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_register(0x0022, value)

   def setThreshold(self, value, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_register(0x002D, value)

   def getThreshold(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      return d.read_register(0x002D)

   def getAlarm(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      return d.read_register(0x002E)

   def getVref(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      return d.read_register(0x002C)

   def powerOn(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_bit(1, True)

   def powerOff(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_bit(1, False)

   def reset(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_bit(2, True)

   def getInfo(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      fwver = d.read_string(0x0002, 1)
      pmtsn = d.read_string(0x0008, 6)
      hvsn = d.read_string(0x000E, 6)
      febsn = d.read_string(0x0014, 6)
      return (fwver, pmtsn, hvsn, febsn)

   def setPMTSerialNumber(self, sn, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_string(0x0008, sn, 6)

   def setHVSerialNumber(self, sn, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_string(0x000E, sn, 6)

   def setFEBSerialNumber(self, sn, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_string(0x0014, sn, 6)

   def setModbusAddress(self, addr, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      d.write_register(0x0000, addr)

   def readMonRegisters(self, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      monData = {}
      baseAddress = 0x0000
      regs = d.read_registers(baseAddress, 48)
      monData['status'] = regs[0x0006]
      monData['Vset'] = regs[0x0026]
      monData['V'] = ((regs[0x002B] << 16) + regs[0x002A]) / 1000
      monData['I'] = ((regs[0x0029] << 16) + regs[0x0028]) / 1000
      monData['T'] = regs[0x0007]
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
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      mlsb = d.read_register(0x0030)
      mmsb = d.read_register(0x0031)
      calibm = ((mmsb << 16) + mlsb)
      calibm = struct.unpack('l', struct.pack('L', calibm & 0xffffffff))[0]
      calibm = calibm / 10000

      qlsb = d.read_register(0x0032)
      qmsb = d.read_register(0x0033)
      calibq = ((qmsb << 16) + qlsb)
      calibq = struct.unpack('l', struct.pack('L', calibq & 0xffffffff))[0]
      calibq = calibq / 10000

      calibt = d.read_register(0x0034)
      calibt = calibt / 1.6890722

      return (calibm, calibq, calibt)

   def writeCalibSlope(self, slope, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      slope = int(slope * 10000)
      lsb = (slope & 0xFFFF)
      msb = (slope >> 16) & 0xFFFF

      d.write_register(0x0030, lsb)
      d.write_register(0x0031, msb)

   def writeCalibOffset(self, offset, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      offset = int(offset * 10000)
      lsb = (offset & 0xFFFF)
      msb = (offset >> 16) & 0xFFFF

      d.write_register(0x0032, lsb)
      d.write_register(0x0033, msb)
   
   def writeCalibDiscr(self, discr, devnum=None):
      if devnum: d = self.devset[devnum]
      else: d = self.dev
      discr = int(discr * 1.6890722)

      d.write_register(0x0034, discr)
