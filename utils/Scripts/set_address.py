import sys
import mmap
import minimalmodbus
import time

def checkRegBoundary(addr):
    if (addr < 0 or addr > 50):
        return False
    return True

def do_read(address) -> None:
    """Read UIO register"""
    if (checkRegBoundary(address)):
        value = int.from_bytes(regs[address * 4:(address * 4) + 4], byteorder='little')
        print(f'0x{value:08x} ({value})')
    else:
        print(f'E: register address outside boundary - min:0 max:{50}')

def do_write(address, value) -> None:
  """Write UIO register"""
  if (checkRegBoundary(address)):
     try:
        regs[address*4:(address*4)+4] = int.to_bytes(value, 4, byteorder='little')
     except:
        print(f'E: write register error')
  else:
     print(f'E: register address outside boundary - min:0 max:{50}')

def open_serial(serial, addr):
     dev = minimalmodbus.Instrument(serial, addr)
     dev.serial.baudrate = 115200
     dev.serial.timeout = 0.5
     dev.mode = minimalmodbus.MODE_RTU
     return dev

if __name__ == '__main__':

    try:
        fid = open("/dev/uio0", 'r+b', 0)
    except:
        print("E: UIO device /dev/uio0 not found")
        sys.exit(-1)
    
    regs = mmap.mmap(fid.fileno(), 0x10000)
    
    for i in range(1, 20):
        do_write(1, 2**(i-1))
        do_read(1)
        print(f'Acceso socket {i}')
        time.sleep(1)
        try:
            FEB = open_serial('/dev/ttyPS2', 20)
            FEB.write_register(0x0000, i)
            print(f'Indirizzo {i} cambiato')
        except:
            print('Scheda non trovata')
        time.sleep(1)
    do_write(1, 0)
