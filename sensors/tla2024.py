#!/usr/bin/env python3

import smbus2
import time
import sys
import ctypes
c_uint8 = ctypes.c_uint8
c_uint16 = ctypes.c_uint16

# Configuration Register bits fields
class CR_bits(ctypes.LittleEndianStructure):
    _fields_ = [
    ("reserved",     c_uint8, 5),
    ("dr",           c_uint8, 3),
    ("mode",         c_uint8, 1),
    ("pga",          c_uint8, 3),
    ("mux",          c_uint8, 3),
    ("os",           c_uint8, 1),
]

class CR(ctypes.Union):
    _anonymous_ = ("bit",)
    _fields_ = [
        ("bit",    CR_bits),
        ("asWord", c_uint16)
    ]

class TLA2024:

   _CDR = 0x00
   _CR = 0x01

   def __init__(self, bus, address):
      self.bus = bus
      self.address = address
      try:
         self.i2cbus = smbus2.SMBus(bus)
      except IOError:
         print(f"E: I2C bus {bus} not found")
         sys.exit(-1)

   def readConfRegister(self):
      data = self.i2cbus.read_i2c_block_data(self.address, self._CR, 2)
      return (data[0] << 8) + data[1]

   def writeConfRegister(self, data):
      msb = (data & 0xFF00) >> 8
      lsb = (data & 0x00FF)
      self.i2cbus.write_i2c_block_data(self.address, self._CR, [msb, lsb])

   def readDataRegister(self):
      data = self.i2cbus.read_i2c_block_data(self.address, self._CDR, 2)
      return ((data[0] << 8) + data[1]) >> 4

   def isReady(self):
      return (self.readConfRegister() & 0x8000)

   def readAll(self):
      output = []
      mux = [ 0b100, 0b101, 0b110, 0b111 ]
      cr = CR()
      cr.os = 1         # start conversion
      cr.pga = 0b001    # FSR = +/- 4.096V - LSB size 2mV
      cr.mode = 1       # single shot conversion mode
      cr.dr = 0b100     # data rate 1600 SPS
      cr.reserved = 3   # fixed value

      for value in mux:
         cr.mux = value
         self.writeConfRegister(cr.asWord)
         while (not self.isReady()):
            None
         # append value in mV
         output.append(self.readDataRegister() * 2)   

      return output

def main():
   tla = TLA2024(1, 0x48)
   print(tla.readAll())

if __name__=="__main__":
   main()
