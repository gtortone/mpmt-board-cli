
import os
import re
import mmap

REG_FW_DATE_AND_FAULTS = 61
REG_FW_TIME = 62
REG_FW_SHA = 63
REG_FW_VARIANT = 103
REG_FW_VERSION = 104

class FPGADevice:

   def __init__(self, uiodev):
      try:
         self.fid = open(uiodev, 'r+b', 0)
      except FileNotFoundError:
         self.perror("UIO device not found")
         sys.exit(-1)

      self.regs = mmap.mmap(self.fid.fileno(), 0x10000)

   def read_register(self, add) -> int:
      return int.from_bytes(self.regs[add*4:(add*4)+4], byteorder='little')

   def write_register(self, add, value) -> None:
      self.regs[add*4:(add*4)+4] = int.to_bytes(value, 4, byteorder='little') 

   def getFirmwareInfo(self) -> dict[str, str]:
      dateValue = self.read_register(REG_FW_DATE_AND_FAULTS)
      timeValue = self.read_register(REG_FW_TIME)
      shaValue = self.read_register(REG_FW_SHA)
      versionValue = self.read_register(REG_FW_VERSION)
      variantValue = self.read_register(REG_FW_VARIANT)
   
      dateHex = f"{dateValue:08x}"
      timeHex = f"{timeValue:08x}"
      versionHex = f"{versionValue:08x}"
   
      major = int(versionHex[:2])
      minorText = versionHex[2:4]
      patchText = versionHex[4:] or "0"
      minor = int(minorText, 16)
      patch = int(patchText, 16)
      version = f"v{major}.{minor}.{patch}"
      variant = "PLAIN" if variantValue == 0x7FFFF else "LED"
   
      return {
          "version": version,
          "bitstreamDate": f"{dateHex[6:8]}-{dateHex[4:6]}-{dateHex[0:4]}",
          "bitstreamTime": f"{timeHex[0:2]}:{timeHex[2:4]}:{timeHex[4:6]}",
          "commitSha": f"{shaValue:08x}",
          "variant": f"{variant}"
      }
