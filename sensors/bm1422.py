from smbus2 import SMBus
import time

I2C_ADDR = 0x0E  # tipico per BM1422AGMV

# Registri principali (BM1422AGMV)
REG_WIA = 0x0F       # Who Am I
REG_CNTL1 = 0x1B
REG_CNTL2 = 0x1C
REG_CNTL3 = 0x1D
REG_CNTL4_1 = 0x5C
REG_CNTL4_2 = 0x15D
REG_DATA = 0x10      # inizio dati (6 byte)

EXPECTED_ID = 0x41   # valore tipico WIA

def init_sensor(bus):
    bus.write_byte_data(I2C_ADDR, REG_CNTL1, 0x80)
    time.sleep(0.05)

    bus.write_byte_data(I2C_ADDR, REG_CNTL4_1, 0x0)
    time.sleep(0.05)

    bus.write_byte_data(I2C_ADDR, REG_CNTL4_2, 0x00)
    time.sleep(0.05)

    bus.write_byte_data(I2C_ADDR, REG_CNTL2, 0xC)
    time.sleep(0.05)

    bus.write_byte_data(I2C_ADDR, REG_CNTL3, 0x40)
    time.sleep(0.05)

def read_xyz(bus):
    data = bus.read_i2c_block_data(I2C_ADDR, REG_DATA, 6)

    # 16-bit signed
    x = (data[1] << 8) | data[0]
    y = (data[3] << 8) | data[2]
    z = (data[5] << 8) | data[4]

    # conversione signed
    def to_signed(val):
        return val - 65536 if val > 32767 else val

    return to_signed(x), to_signed(y), to_signed(z)

def main():
    with SMBus(1) as bus:
        # verifica ID
        wia = bus.read_byte_data(I2C_ADDR, REG_WIA)
        print(f"WIA: 0x{wia:02X}")

        if wia != EXPECTED_ID:
            print("⚠️ ID inatteso, controlla collegamenti/I2C addr")
        else:
            print("Sensore rilevato 👍")

        init_sensor(bus)

        print("Lettura magnetometro:")

        while True:
            x, y, z = read_xyz(bus)
            print(f"X: {x}  Y: {y}  Z: {z}")
            time.sleep(0.5)

if __name__ == "__main__":
    main()