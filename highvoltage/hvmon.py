#!/usr/bin/env python3
# coding=utf-8

import argparse
import copy
import csv
import os
import datetime
import time
import sys
from cmd2.table_creator import (
    Column,
    SimpleTable,
    HorizontalAlignment
)
from typing import (
    List,
)
from hvmodbus import HVModbus

def alarmString(alarmCode):
    msg = ' '
    if (alarmCode == 0):
        return 'none'
    if (alarmCode & 1):
        msg = msg + 'OV '
    if (alarmCode & 2):
        msg = msg + 'UV '
    if (alarmCode & 4):
        msg = msg + 'OC '
    if (alarmCode & 8):
        msg = msg + 'OT '
    return self.alarm_red(msg)

def statusString(statusCode):
    if (statusCode == 0):
        return 'UP'
    elif (statusCode == 1):
        return 'DOWN'
    elif (statusCode == 2):
        return 'RUP'
    elif (statusCode == 3):
        return 'RDN'
    elif (statusCode == 4):
        return 'TUP'
    elif (statusCode == 5):
        return 'TDN'
    elif (statusCode == 6):
        return 'TRIP'
    else:
        return 'undef'

def printHeader():
    print(st.generate_data_row(['addr','status','Vset','V','I','T','rate UP/DN','limit V/I/T/TRIP','trigger thr','alarm']))
    print(st.generate_data_row(['','','[V]','[V]','[uA]','[°C]','[V/s]/[V/s]','[V]/[uA]/[°C]/[s]','[mV]','']))

parser = argparse.ArgumentParser()
parser.add_argument('--mode', default='rtu', const='rtu', nargs='?', choices=['rtu', 'tcp'], help='set modbus interface (default: %(default)s)') 
parser.add_argument('--host', action='store', type=str, help='mbusd hostname (default: localhost)', default='localhost')
parser.add_argument('--port', action='store', type=str, help='serial port device (default: /dev/ttyPS1)', default='/dev/ttyPS1')
parser.add_argument('--freq', action='store', type=int, help='monitoring frequency (default: 1 second)', default=1)
parser.add_argument('-m', '--modules', help='comma-separated list of modules to monitor', required=True)
parser.add_argument('-f', '--filename', action='store', type=str, help='output filename')
parser.add_argument('-l', '--filelabel', action='store', type=str, help='output filename <label>-<YYYYMMDD>-<HHMM>.csv')
args = parser.parse_args()

if args.filename is None and args.filelabel is None:
    print('E: filename (-f) or filelabel (-l) option is required')
    sys.exit(-1)

try:
    hvModList = [int(x) for x in args.modules.split(",")]
except:
    raise ValueError('E: failed to parse --modules - should be comma-separated list of integers')

hvList = []
for addr in hvModList:
    hv = HVModbus(args)
    res = hv.open(addr)
    if res != True:
        print(f'E: failed to open module {addr}')
        sys.exit(-1)
    else:
        hvList.append(copy.copy(hv))
        print(f'I: module {addr} ok')

if args.filename:
    fname = args.filename
elif args.filelabel:
    d = datetime.datetime.now()
    fname = args.filelabel + '-' + str(d.year) + str(d.month) + str(d.day) + '-' + str(d.hour) + str(d.minute) + '.csv'

if os.path.exists(fname):
    while True:
        res = input(f'I: file {fname} exists - do you want overwrite (Y/N)')
        if res.lower() == 'y':
            break
        elif res.lower() == 'n':
            print('E: specify different filename')
            sys.exit(-1)

try:
    fhand = open(fname, 'w')
except Exception as e:
    print(f'E: output file open error - {e}')
    sys.exit(-1)

print(f'I: output filename: {fname}')

fields = list(hv.readMonRegisters().keys())
fields.insert(0, 'timestamp')
fields.insert(1, 'time')
fields.insert(2, 'address')
writer = csv.DictWriter(fhand, fields, dialect='excel')
writer.writeheader()

columns: List[Column] = list()
columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.RIGHT))
columns.append(Column("", width=6, data_horiz_align=HorizontalAlignment.CENTER))
columns.append(Column("", width=5, data_horiz_align=HorizontalAlignment.RIGHT))
columns.append(Column("", width=9, data_horiz_align=HorizontalAlignment.RIGHT))
columns.append(Column("", width=7, data_horiz_align=HorizontalAlignment.RIGHT))
columns.append(Column("", width=7, data_horiz_align=HorizontalAlignment.RIGHT))
columns.append(Column("", width=12, data_horiz_align=HorizontalAlignment.RIGHT))
columns.append(Column("", width=20, data_horiz_align=HorizontalAlignment.RIGHT))
columns.append(Column("", width=13, data_horiz_align=HorizontalAlignment.RIGHT))
columns.append(Column("", width=14, data_horiz_align=HorizontalAlignment.CENTER))

st = SimpleTable(columns, divider_char=None)
try:
    i = 1
    while True:
        start = datetime.datetime.now()
        printHeader()
        for hv in hvList:
            try:
                mon = hv.readMonRegisters()
            except Exception as e:
                print(f'E: address {hv.address} - {e}')
                continue
            else:
                mon['timestamp'] = int(time.time())
                mon['time'] = datetime.datetime.now()
                mon['address'] = hv.address
                mon['status'] = statusString(mon['status'])
                mon['alarm'] = alarmString(mon['alarm'])
                writer.writerow(mon)
                print(st.generate_data_row([mon['address'], mon['status'], mon['Vset'], f'{mon["V"]:.3f}', f'{mon["I"]:.3f}', mon['T'], f'{mon["rateUP"]}/{mon["rateDN"]}', f'{mon["limitV"]}/{mon["limitI"]}/{mon["limitT"]}/{mon["limitTRIP"]}', mon['threshold'], mon['alarm']]))
                stop = datetime.datetime.now()
                fhand.flush()

        delta = stop - start
        sleep_value = ((args.freq * 1000) - (delta.total_seconds() * 1000)) / 1000
        if sleep_value > 0:
           time.sleep(((args.freq * 1000) - (delta.total_seconds() * 1000)) / 1000)

except KeyboardInterrupt:
    pass

fhand.close()
print(f'I: output file {fname} closed')
print('Bye!')
