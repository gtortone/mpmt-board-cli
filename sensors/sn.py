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

from housekeeping import HouseKeeping, ALIAS_MAP, METRIC_MAP, OPERATION_MAP

def ansi_print(text):
    cmd2.ansi.style_aware_write(sys.stdout, text + '\n')

def printHeader(data):
    print('')
    label = []
    unit = []
    for k, measurements in data.items():
        for m in measurements:
            label.append(m["label"])
            unit.append(m["unit"])
    ansi_print(bright_cyan(st.generate_data_row(label)))
    ansi_print(bright_blue(st.generate_data_row(unit)))

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--continuous', action='store_true', help='continuous mode', default=False)
args = parser.parse_args()

# Text styles used in the data
bright_cyan= functools.partial(cmd2.ansi.style, fg=cmd2.ansi.Fg.LIGHT_CYAN)
bright_blue = functools.partial(cmd2.ansi.style, fg=cmd2.ansi.Fg.LIGHT_BLUE)

hk = HouseKeeping()

data = hk.read()

columns: List[Column] = list()

for k, measurements in data.items():
    # alias to I2C address (e.g. "tla2024" => 0x48)
    address = {v: k for k, v in ALIAS_MAP.items()}.get(k)
    m = METRIC_MAP[address]
    for info in m:
        columns.append(Column("", width=info.width, data_horiz_align=HorizontalAlignment.RIGHT))
    if OPERATION_MAP.get(address, None):
        m = OPERATION_MAP[address]
        for info in m:
            columns.append(Column("", width=info.width, data_horiz_align=HorizontalAlignment.RIGHT))

st = SimpleTable(columns, divider_char=None)

i = 0
while True:

    data = hk.read()

    if i % 20 == 0:
        printHeader(data)
        i = 0

    row = []

    for k, measurements in data.items():
        for m in measurements:
            row.append(m["value"])

    ansi_print(st.generate_data_row(row))

    i = i + 1

    time.sleep(1)

    if not args.continuous:
        break
