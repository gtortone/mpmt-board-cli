import smbus2
import time

class LSM303Magnet:

    # --- Magnetometer (LSM303AGR) registers ---
    WHO_AM_I_M   = 0x4F
    CFG_REG_A_M  = 0x60
    CFG_REG_B_M  = 0x61
    CFG_REG_C_M  = 0x62
    OUTX_L_REG_M = 0x68  # X_L..Z_H = 0x68..0x6D

    # LSM303AGR sensitivity: 1.5 mG/LSB = 0.15 µT/LSB
    SCALE = 0.15  # µT per LSB

    def __init__(self, bus, address):
        self.bus = bus
        self.address = address
        try:
            self.i2cbus = smbus2.SMBus(bus)
        except IOError:
            print(f"E: I2C bus {bus} not found")
            sys.exit(-1) 

        # CFG_REG_A_M (0x60): [7]=COMP_TEMP_EN (deve stare a 1), [3:2]=ODR, [1:0]=MD
        # temp compensation ON, ODR=10Hz (00), continuous mode MD=00
        self.i2cbus.write_byte_data(self.address, self.CFG_REG_A_M, 0x80)

        # CFG_REG_B_M: default (offset canc / LPF off)
        self.i2cbus.write_byte_data(self.address, self.CFG_REG_B_M, 0x00)

        # CFG_REG_C_M: BDU=1 (bit4) coherent readings (datasheet: CFG_REG_C_M)
        self.i2cbus.write_byte_data(self.address, self.CFG_REG_C_M, 0x10)

    @staticmethod
    def _int16(lo: int, hi: int) -> int:
        v = (hi << 8) | lo
        return v - 65536 if v & 0x8000 else v

    def _read_block(self, addr: int, start_reg: int, n: int) -> bytes:
        data = self.i2cbus.read_i2c_block_data(addr, start_reg, n)
        return bytes(data)

    def readAll(self):
        output = []
        # OUTX_L_REG_M..OUTZ_H_REG_M = 6 bytes
        d = self._read_block(self.address, self.OUTX_L_REG_M, 6)
        output.append(self._int16(d[0], d[1]) * self.SCALE)  # X
        output.append(self._int16(d[2], d[3]) * self.SCALE)  # Y
        output.append(self._int16(d[4], d[5]) * self.SCALE)  # Z
        return output

class LSM303Accel:

    # --- Accelerometer (LIS2DH-like) registers ---
    WHO_AM_I_A   = 0x0F
    CTRL_REG1_A  = 0x20
    CTRL_REG4_A  = 0x23
    OUT_X_L_A    = 0x28  # auto-increment via bit 0x80 in I2C

    def __init__(self, bus, address):
        self.bus = bus
        self.address = address
        try:
            self.i2cbus = smbus2.SMBus(bus)
        except IOError:
            print(f"E: I2C bus {bus} not found")
            sys.exit(-1) 

        # 100 Hz, enable X/Y/Z (0b0101_0111)
        self.i2cbus.write_byte_data(self.address, self.CTRL_REG1_A, 0x57)
        # BDU=1 (bit7) + HR=1 (bit3) => 0b1000_1000
        self.i2cbus.write_byte_data(self.address, self.CTRL_REG4_A, 0x88)

    @staticmethod
    def _int16(lo: int, hi: int) -> int:
        v = (hi << 8) | lo
        return v - 65536 if v & 0x8000 else v

    def _read_block(self, addr: int, start_reg: int, n: int) -> bytes:
        data = self.i2cbus.read_i2c_block_data(addr, start_reg, n)
        return bytes(data)

    def readAll(self):
        output = []
        # auto-increment: OR 0x80 on start register
        d = self._read_block(self.address, self.OUT_X_L_A | 0x80, 6)
        output.append(self._int16(d[0], d[1]) / 9.81)  # X
        output.append(self._int16(d[2], d[3]) / 9.81)  # Y
        output.append(self._int16(d[4], d[5]) / 9.81)  # Z
        return output
