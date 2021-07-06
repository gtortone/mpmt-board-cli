#!/usr/bin/env python3
# coding=utf-8

import sys
import time
import argparse
import cmd2
import functools
from cmd2.table_creator import (
    Column,
    SimpleTable,
    HorizontalAlignment
)
from typing import (
    List,
)
from bme280 import BME280
from bmx160 import BMX160
from tla2024 import TLA2024

def ansi_print(text):
   cmd2.ansi.style_aware_write(sys.stdout, text + '\n')

def printHeader():
   print('')
   label = ['+5.0V','+3.3V','IpoeA','IpoeB','PpoeA','PpoeB','T','P','H']
   unit = ['[V]','[V]','[A]','[A]','[W]','[W]','[°C]','[hPa]','[%Rh]']
   if(bmeExt is not None):
      label.extend(['Text','Pext'])
      unit.extend(['[°C]','[hPa]'])
      if(bmeExt.readId() == 0x96):      # BME280
         label.append('Hext')
         unit.append('[%Rh]')
   if(args.bmx):
      label.extend(['Magn X/Y/Z','Gyro X/Y/Z','Accel X/Y/Z'])
      unit.extend(['[uT]','[g]','[m/s^2]'])

   ansi_print(bright_cyan(st.generate_data_row(label)))
   ansi_print(bright_blue(st.generate_data_row(unit)))

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--continuous', action='store_true', help='continuous mode', default=False)
parser.add_argument('--bmx', action='store_true', help='include BMX160 metrics', default=False)
args = parser.parse_args()

# Text styles used in the data
bright_cyan= functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_cyan)
bright_blue = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_blue)

# BME280 on-board sensor
bme = BME280(1, 0x76)

# BME280 external sensor
bmeExt = BME280(1, 0x77)
try:
   bmeExt.readId()
except IOError:
   bmeExt = None

columns: List[Column] = list()
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # 5.0V
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # 3.3V
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # IpoeA
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # IpoeB
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # PpoeA
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # PpoeB
columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.RIGHT))  # T
columns.append(Column("", width=7, data_horiz_align=HorizontalAlignment.RIGHT))  # P
columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.RIGHT))  # H
if(bmeExt is not None):
   columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.RIGHT))  # Text
   columns.append(Column("", width=7, data_horiz_align=HorizontalAlignment.RIGHT))  # Pext
   if(bmeExt.readId() == 0x96):      # BME280
      columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.RIGHT))  # Hext
if(args.bmx):
   columns.append(Column("", width=16, data_horiz_align=HorizontalAlignment.RIGHT))  # Magn X/Y/Z
   columns.append(Column("", width=16, data_horiz_align=HorizontalAlignment.RIGHT))  # Gyro X/Y/Z
   columns.append(Column("", width=16, data_horiz_align=HorizontalAlignment.RIGHT))  # Accel X/Y/Z

st = SimpleTable(columns, divider_char=None)

i = 0
while (True):

   if (i % 20 == 0):
      printHeader()
      i = 0

   row = []

   tla = TLA2024(1, 0x48)
   tlaData = tla.readAll()
   V1 = (tlaData[0] * 3 / 1000)  # AIN0 - +5V
   row.append(f'{V1:.3f}')
   V2 = (tlaData[2] * 2 / 1000)  # AIN2 - +3.3V
   row.append(f'{V2:.3f}')
   I1 = tlaData[1]/1000          # AIN1 - Imon1
   row.append(f'{I1:.3f}')
   I2 = tlaData[3]/1000          # AIN3 - Imon2
   row.append(f'{I2:.3f}')
   P1 = V1 * I1
   P2 = V1 * I2
   row.append(f'{P1:.3f}')
   row.append(f'{P2:.3f}')

   bmeData = bme.readAll()
   row.append(f'{bmeData[0]:.2f}')
   row.append(f'{bmeData[1]:.2f}')
   row.append(f'{bmeData[2]:.2f}')

   if(bmeExt is not None):
      bmeData = bmeExt.readAll()
      row.append(f'{bmeData[0]:.2f}')
      row.append(f'{bmeData[1]:.2f}')
      if(bmeExt.readId() == 0x96):      # BME280
         row.append(f'{bmeData[2]:.2f}')

   if(args.bmx):
      bmx = BMX160(1, 0x69)
      bmxData = bmx.readAll()
      row.append(f'{bmxData[0]:.0f}/{bmxData[1]:.0f}/{bmxData[2]:.0f}')
      row.append(f'{bmxData[3]:.1f}/{bmxData[4]:.1f}/{bmxData[5]:.1f}')
      row.append(f'{bmxData[6]:.1f}/{bmxData[7]:.1f}/{bmxData[8]:.1f}')

   ansi_print(st.generate_data_row(row))

   i = i + 1

   time.sleep(1)

   if(not args.continuous):
      break
