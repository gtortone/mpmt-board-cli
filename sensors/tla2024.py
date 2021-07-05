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
      vfs = [ 0b000, 0b010, 0b001, 0b010 ]   # AIN0: 6.144V, AIN1: 2.048V, AIN2: 4.096V, AIN3: 2.048V
      mul = [ 3, 1, 2, 1 ]                   # AIN0: 3mV/LSB, AIN1: 1mV/LSB, AIN2: 2mV/LSB, AIN3: 1mV/LSB
      cr = CR()
      cr.os = 1         # start conversion
      cr.mode = 1       # single shot conversion mode
      cr.dr = 0b100     # data rate 1600 SPS
      cr.reserved = 3   # fixed value

      for i in range(0,4):
         cr.mux = mux[i]
         cr.pga = vfs[i]
         self.writeConfRegister(cr.asWord)
         while (not self.isReady()):
            None
         # append value in mV
         output.append(self.readDataRegister() * mul[i])   

      return output

def main():
   tla = TLA2024(1, 0x48)
   print(tla.readAll())

if __name__=="__main__":
   main()
