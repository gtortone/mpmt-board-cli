#!/usr/bin/env python3

import sys
import mmap
import subprocess
import argparse
import time

try:
    fid = open('/dev/uio0', 'r+b', 0)
except FileNotFoundError:
    perror("UIO device not found")
    sys.exit(-1)

regs = mmap.mmap(fid.fileno(), 0x10000)

def write(add: int, value: int) -> None:
    global regs
    regs[add*4:(add*4)+4] = int.to_bytes(value, 4, byteorder='little')

def read(add: int) -> int:
    global regs
    return int.from_bytes(regs[add*4:(add*4)+4], byteorder='little')

def program_feb(addr: int, firmware:str) -> None:
    print(f"Turning on channel {addr}")
    write(0, (1<<(addr-1)))
    time.sleep(1)
    write(1, (1<<(addr-1)))
    time.sleep(3)

    print(f'Start programming FEB {addr}')
    res = subprocess.run(['stm32flash',  '-b', '115200', '-w', f'{firmware}', '-e', '255', '-v', '/dev/ttyPS1'], shell=False)

    time.sleep(1)
    write(0, 0)
    time.sleep(1)
    write(1, 0)

    return res.returncode

def main(FEBnum: str, firmwarename: str) -> None:
    if FEBnum == 'all':
        febnum = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    elif not parser_args.numberFEB:
        print('No FEB selected')
        sys.exit(-1)
    else:
        febnum = FEBnum.split(",")

    for i in febnum:
        res = program_feb(int(i), firmwarename)
        if res != 0:
            print(f'FEB {i} programming FAILED')
            print(f'(ModBus services running ? (mpmt-mss, ...)')
        else:
            print(f'FEB {i} programming OK')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--numberFEB', help='FEB addres that will be flashed separated by comma (write all for all 19)')
    parser.add_argument('-f', '--filename', help='Firmware .hex')
    parser_args = parser.parse_args()

    main(parser_args.numberFEB, parser_args.filename)
