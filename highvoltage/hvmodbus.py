import minimalmodbus

class HVModbus():
   def __init__(self):
      self.dev = None
      self.address = None

   def open(self, serial, addr):
      if (self.probe(serial, addr)):
         self.dev = minimalmodbus.Instrument(serial, addr)
         self.dev.serial.baudrate = 9600
         self.dev.serial.timeout = 0.5
         self.dev.mode = minimalmodbus.MODE_RTU
         #self.dev.debug = True
         self.address = addr
         return True
      else:
         return False

   def probe(self, serial, addr):
      dev =  minimalmodbus.Instrument(serial, addr)
      dev.serial.baudrate = 9600
      dev.serial.timeout = 0.5
      dev.mode = minimalmodbus.MODE_RTU

      found = False
      for _ in range(0,3):
         try:
            dev.read_register(0x00)  # read modbus address register
            found = True
            break;
         except IOError:
            None

      return found

   def isConnected(self):
      return (self.address is not None)

   def getAddress(self):
      return self.address

   def getStatus(self):
      return self.dev.read_register(0x0006)

   def getVoltage(self):
      lsb = self.dev.read_register(0x002A)
      msb = self.dev.read_register(0x002B)
      value = (msb << 16) + lsb
      return (value / 1000)

   def getVoltageSet(self):
      return self.dev.read_register(0x0026)

   def setVoltageSet(self, value):
      self.dev.write_register(0x0026, value)

   def getCurrent(self):
      lsb = self.dev.read_register(0x0028)
      msb = self.dev.read_register(0x0029)
      value = (msb << 16) + lsb
      return (value / 1000)

   def getTemperature(self):
      return self.dev.read_register(0x0007)

   def getRate(self, fmt=str):
      rup = self.dev.read_register(0x0023)
      rdn = self.dev.read_register(0x0024)
      if (fmt == str):
         return f'{rup}/{rdn}' 
      else:
         return (rup, rdn)

   def setRateRampup(self, value):
      self.dev.write_register(0x0023, value, functioncode=6)

   def setRateRampdown(self, value):
      self.dev.write_register(0x0024, value)

   def getLimit(self, fmt=str):
      lv = self.dev.read_register(0x0027)
      li = self.dev.read_register(0x0025)
      lt = 0 # self.dev.read_register(0x002F)
      ltt = self.dev.read_register(0x0022)
      if (fmt == str):
         return f'{lv}/{li}/{lt}/{ltt}'
      else:
         return (lv, li, lt, ltt)

   def setLimitVoltage(self, value):
      self.dev.write_register(0x0027, value)

   def setLimitCurrent(self, value):
      self.dev.write_register(0x0025, value)

   def setLimitTemperature(self, value):
      self.dev.write_register(0x002F, value)

   def setLimitTriptime(self, value):
      self.dev.write_register(0x0022, value)

   def getAlarm(self):
      return self.dev.read_register(0x002E)

   def getVref(self):
      return self.dev.read_register(0x002C)

   def powerOn(self):
      self.dev.write_bit(1, True)

   def powerOff(self):
      self.dev.write_bit(1, False)

   def reset(self):
      self.dev.write_bit(2, True)

   def getInfo(self):
      fwver = self.dev.read_register(0x0002)
      fwmsb = (fwver & 0xFF00) >> 8
      fwlsb = (fwver & 0x00FF)
      pmsn = self.dev.read_string(0x0008, 6)
      hvsn = self.dev.read_string(0x000E, 6)
      pcbsn = self.dev.read_string(0x0014, 6)
      return (fwmsb, fwlsb, pmsn, hvsn, pcbsn)