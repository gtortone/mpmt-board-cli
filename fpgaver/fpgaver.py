#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from FPGADevice import FPGADevice

fpga = FPGADevice('/dev/uio0')

ver = fpga.getFirmwareInfo()

#{'version': 'v0.0.0', 'bitstreamDate': '06-10-2026', 'bitstreamTime': '14:57:23', 'commitSha': '7f902e93'}
print(f"\n# FPGA bitstream: release/tag: {ver['version']}, build: {ver['bitstreamDate']}/{ver['bitstreamTime']}, commit: {ver['commitSha']}, variant: {ver['variant']}\n")

