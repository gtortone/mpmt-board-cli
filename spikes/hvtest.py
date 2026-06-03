#!/usr/bin/env python3

from pymodbus.client import ModbusSerialClient

from pymodbus import (
    FramerType,
    ModbusException,
)

client = ModbusSerialClient(
    port="/dev/ttyPS1",
    framer=FramerType.RTU,
    baudrate=115200,
    parity="N",
    stopbits=1,
    bytesize=8,
    timeout=0.1
)

connection = client.connect()

if connection:

    for i in range(1000):

       rr = client.read_holding_registers(
           address=0x2A,
           count=2,
           device_id=1
       )

       if not rr.isError():
           rr.registers.reverse()
           value = client.convert_from_registers(rr.registers, data_type=client.DATATYPE.INT32) / 1000
           print("value:", value)
       else:
           print("error")

    client.close()
else:
    print("Connection failed")
