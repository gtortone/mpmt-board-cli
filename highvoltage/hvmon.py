#!/usr/bin/env python3
# coding=utf-8

import argparse
import copy
import csv
import os
import datetime
import time
import sys
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

parser = argparse.ArgumentParser()
parser.add_argument('--port', action='store', type=str, help='serial port device (default: /dev/ttyPS1)', default='/dev/ttyPS1')
parser.add_argument('--freq', action='store', type=int, help='monitoring frequency (default: 1 second)', default=1)
parser.add_argument('-m', '--modules', help='comma-separated list of modules to monitor', required=True)
parser.add_argument('-f', '--filename', action='store', type=str, help='output filename', required=True)
args = parser.parse_args()

try:
    hvModList = [int(x) for x in args.modules.split(",")]
except:
    raise ValueError('E: failed to parse --modules - should be comma-separated list of integers')

hvList = []
for addr in hvModList:
    hv = HVModbus()
    res = hv.open(args.port, addr)
    if res != True:
        print(f'E: failed to open module {addr}')
        sys.exit(-1)
    else:
        hvList.append(copy.copy(hv))
        print(f'I: module {addr} ok')

if os.path.exists(args.filename):
    while True:
        res = input(f'I: file {args.filename} exists - do you want overwrite (Y/N)')
        if res.lower() == 'y':
            break
        elif res.lower() == 'n':
            print('E: specify different filename')
            sys.exit(-1)

try:
    fhand = open(args.filename, 'w')
except Exception as e:
    print(f'E: output file open error - {e}')
    sys.exit(-1)

fields = list(hv.readMonRegisters().keys())
fields.insert(0, 'timestamp')
fields.insert(1, 'time')
fields.insert(2, 'address')
writer = csv.DictWriter(fhand, fields, dialect='excel')
writer.writeheader()

try:
    while True:
        start = datetime.datetime.now()
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
                print(list(mon.values()))
                writer.writerow(mon)
                stop = datetime.datetime.now()

        delta = stop - start
        time.sleep(((args.freq * 1000) - (delta.total_seconds() * 1000)) / 1000)

except KeyboardInterrupt:
    pass

fhand.close()
print(f'I: output file {args.filename} closed')
print('Bye!')
