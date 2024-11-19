import sys
import mmap
import minimalmodbus
import time

def do_read(address, regs) -> None:
    """Read UIO register"""
    if (checkRegBoundary(address)):
        value = int.from_bytes(regs[address * 4:(address * 4) + 4], byteorder='little')
        #print(f'0x{value:08x} ({value})')
    else:
        print(f'E: register address outside boundary - min:0 max:{50}')
    return value

def do_write(address, value, regs) -> None:
  """Write UIO register"""
  if (checkRegBoundary(address)):
     try:
        regs[address*4:(address*4)+4] = int.to_bytes(value, 4, byteorder='little')
     except:
        print(f'E: write register error')
  else:
     print(f'E: register address outside boundary - min:0 max:{50}')

def checkRegBoundary(addr):
    if (addr < 0 or addr > 50):
        return False
    return True

def turnmPMTon(regs):
    do_write(1, 0xf, regs)
    do_read(1, regs)
    print('Turn on 1 to 4')
    time.sleep(2)
    do_write(1, 0xff, regs)
    do_read(1, regs)
    print('Turn on 5 to 8')
    time.sleep(2)
    do_write(1, 0xfff, regs)
    do_read(1, regs)
    print('Turn on 9 to 12')
    time.sleep(2)
    do_write(1, 0xffff, regs)
    do_read(1, regs)
    print('Turn on 13 to 16')
    time.sleep(2)
    do_write(1, 0x7ffff, regs)
    do_read(1, regs)
    print('Turn on 17 to 19')

def turnmPMToff(regs):
    do_write(1, 0, regs)
    do_read(1, regs)
    print('Tutte spente')

if __name__ == '__main__':

    try:
        fid = open('/dev/uio0', 'r+b', 0)
    except:
        print("E: UIO device /dev/uio0 not found")
        sys.exit(-1)

    regs = mmap.mmap(fid.fileno(), 0x10000)
    turnmPMTon(regs)
