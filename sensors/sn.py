#!/usr/bin/env python3
# coding=utf-8

import sys
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

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--continuous', action='store_true', help='continuous mode', default=False)
args = parser.parse_args()

# Text styles used in the data
bright_black = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_black)
bright_yellow = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_yellow)
bright_green = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_green)
bright_red = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_red)
bright_cyan= functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_cyan)
bright_blue = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_blue)
yellow = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.yellow)
blue = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.fg.bright_blue)

columns: List[Column] = list()
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # 5.0V
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # 3.3V
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # IpoeA
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))  # IpoeB
columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.RIGHT))  # T
columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.RIGHT))  # P
columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.RIGHT))  # H
columns.append(Column("", width=20, data_horiz_align=HorizontalAlignment.RIGHT))  # Magn X/Y/Z
columns.append(Column("", width=20, data_horiz_align=HorizontalAlignment.RIGHT))  # Gyro X/Y/Z
columns.append(Column("", width=20, data_horiz_align=HorizontalAlignment.RIGHT))  # Accel X/Y/Z

st = SimpleTable(columns, divider_char=None)

def ansi_print(text):
   cmd2.ansi.style_aware_write(sys.stdout, text + '\n')

def printHeader():
   print('')
   ansi_print(bright_cyan(st.generate_data_row(['+5.0V','+3.3V','IpoeA','IpoeB','T','P','H','Magn X/Y/Z','Gyro X/Y/Z','Accel X/Y/Z'])))
   ansi_print(bright_blue(st.generate_data_row(['[V]','[V]','[mA]','[mA]','[°C]','[hPa]','[%Rh]','[uT]','[g]','[m/s^2]'])))


i = 0
while (True):

   if (i % 20 == 0):
      printHeader()

   row = []

   tla = TLA2024(1, 0x48)
   tlaData = tla.readAll()
   value = (tlaData[0] * 3 / 2 / 1000)  # AIN0 - +5V
   row.append(f'{value:.3f}')
   value = (tlaData[2] * 2 / 1000)      # AIN2 - +3.3V
   row.append(f'{value:.3f}')
   value = 0 #tlaData[1]                   # AIN1 - Imon1
   row.append(f'{value:.3f}')
   value = 0 #tlaData[3]                   # AIN3 - Imon2
   row.append(f'{value:.3f}')

   bme = BME280(1, 0x76)
   bmeData = bme.readAll()
   row.append(f'{bmeData[0]:.2f}')
   row.append(f'{bmeData[1]:.2f}')
   row.append(f'{bmeData[2]:.2f}')

   bmx = BMX160(1, 0x69)
   bmxData = bmx.readAll()
   row.append(f'{bmxData[0]:.0f}/{bmxData[1]:.0f}/{bmxData[2]:.0f}')
   row.append(f'{bmxData[3]:.2f}/{bmxData[4]:.2f}/{bmxData[5]:.2f}')
   row.append(f'{bmxData[6]:.2f}/{bmxData[7]:.2f}/{bmxData[8]:.2f}')

   ansi_print(st.generate_data_row(row))

   i = i + 1

   if(not args.continuous):
      break
