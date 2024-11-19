import sys
import mmap
import subprocess
import argparse
import time


def check_reg_boundary(addr):
    if addr < 0 or addr > 50:
        return False
    return True


def do_write(address, value, regs) -> None:
    if check_reg_boundary(address):
        try:
            regs[address * 4:(address * 4) + 4] = int.to_bytes(value, 4, byteorder='little')
        except:
            print(f'E: write register error')
    else:
        print(f'E: register address outside boundary - min:0 max:{50}')


def do_read(address, regs) -> None:
    if check_reg_boundary(address):
        value = int.from_bytes(regs[address * 4:(address * 4) + 4], byteorder='little')
        print(f'reg {address}: {value} ({bin(value)})')
    else:
        print(f'E: register address outside boundary - min:0 max:{50}')


def program_feb(regs, addr, firmware, port='/dev/ttyPS2', baud='115200') -> None:
    do_write(0, 0, regs)
    time.sleep(0.5)
    do_write(1, 0, regs)
    time.sleep(2)
    do_write(0, 2 ** int(addr), regs)
    time.sleep(0.5)
    do_write(1, 2 ** int(addr), regs)
    do_read(0, regs)
    do_read(1, regs)
    time.sleep(5)

    print(f'Executing stm32flash -b {baud} -w {firmware} -e 255 -v {port}')
    subprocess.run(['stm32flash',  '-b', f'{baud}', '-w', f'{firmware}', '-e', '255',
                    '-v', f'{port}'], shell=False)

    time.sleep(0.5)
    do_write(0, 0, regs)
    time.sleep(0.5)
    do_write(1, 0, regs)


def main():
    try:
        fid = open("/dev/uio0", 'r+b', 0)
    except:
        print("E: UIO device /dev/uio0 not found")
        sys.exit(-1)

    registers = mmap.mmap(fid.fileno(), 0x10000)

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--numberFEB',
                        help='FEB addres that will be flashed separated by comma (write all for all 19)')
    parser.add_argument('-f', '--filename', help='Firmware .hex')
    parser.add_argument('-b', '--baud', help='Baudrate')
    parser.add_argument('-p', '--port', help='Serial port')
    parser_args = parser.parse_args()

    if parser_args.numberFEB == 'all':
        febnum = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    elif not parser_args.numberFEB:
        print('No FEB selected')
        sys.exit(-1)
    else:
        febnum = parser_args.numberFEB.split(",")

    for i in febnum:
        program_feb(registers, int(i)-1, parser_args.filename, parser_args.port, parser_args.baud)
        print(f'FEB {int(i)-1} programmata')


if __name__ == '__main__':
    main()
