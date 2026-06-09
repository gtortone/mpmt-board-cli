
import logging
import pymodbus.client as ModbusClient
from pymodbus import (
    FramerType,
    ModbusException,
)
from multiprocessing import Lock
from dataclasses import dataclass, field
from typing import Literal, Optional

@dataclass
class ModbusConfig:
    mode: Literal["tcp", "rtu"]
    host: Optional[str] = None
    port: Optional[str] = None
    max_slave: int = 21

    def __post_init__(self):
        if self.mode == "tcp" and not self.host:
            raise ValueError("'host' mandatory for tcp mode")
        if self.mode == "rtu" and not self.port:
            raise ValueError("'port' mandatory for rtu mode")
        if self.max_slave < 1:
            raise ValueError("'max_slave' must be >= 1")

class ModbusManager:

    __instance = None

    @staticmethod
    def getInstance():
        if ModbusManager.__instance == None:
            raise Exception("Class ModbusManager - no instance")
        return ModbusManager.__instance

    def __init__(self, param: ModbusConfig):
        if ModbusManager.__instance != None:
            raise Exception("Class ModbusManager - use existing instance")
        else:
            ModbusManager.__instance = self

        self.param = param
        self.client = None
        self.connected = False
        self.mutex = Lock() 
        self.channels = []
        self.max_slave = self.param.max_slave

        logging.getLogger("pymodbus.logging").disabled = True

        if not self.connected:
            if self.param.mode == 'tcp':
                self.client = ModbusClient.ModbusTcpClient(self.param.host, port=502, framer=FramerType.SOCKET)
                if not self.client.connect():
                    raise RuntimeError(f'E: host not reachable or mbusd not running ({self.param.host})')
            elif self.param.mode == 'rtu':
                self.client = ModbusClient.ModbusSerialClient(
                    self.param.port,
                    framer=FramerType.RTU,
                    baudrate=115200,
                    bytesize=8,
                    parity="N",
                    stopbits=1,
                    timeout=0.1
                )
                if not self.client.connect():
                    raise RuntimeError(f'E: port not available ({self.param.port})')

                self.DATATYPE = self.client.DATATYPE
                self.connected = True
                self.probe()

    def close(self):
        if self.connected:
            self.client.close()

    def probe(self):
        for addr in range(1, self.max_slave):
            self.open(addr)

    def check_connect(func):
        def wrapper(self, *args, **kwargs):
            if not self.connected:
                raise RuntimeError("Modbus not connected")
            return func(self, *args, **kwargs)
        return wrapper

    def critical_section(func):
        def wrapper(self, *args, **kwargs):
            self.mutex.acquire()
            try:
                return func(self, *args, **kwargs)
            finally:
                self.mutex.release()
        return wrapper

    @check_connect
    @critical_section
    def open(self, slave: int):
        try:
            rr = self.client.read_holding_registers(address=0, count=1, slave=slave)
        except Exception as e:
            if slave in self.channels:
                self.channels.remove(slave)
            return False

        if (rr is None) or (rr.isError()):
            self.channels.remove(slave)
            return False

        if slave not in self.channels:
            self.channels.append(slave)
        return True

    def getChannels(self) -> list:
        return sorted(self.channels)

    @check_connect
    @critical_section
    def read_holding_registers(self, address: int, count: int, slave: int):
        rr = None
        try:
            rr = self.client.read_holding_registers(address=address, count=count, slave=slave)
        except Exception as e:
            if slave in self.channels:
                self.channels.remove(slave)
            raise(e)
        else:
            if slave not in self.channels:
                self.channels.append(slave)
        return rr

    @check_connect
    @critical_section
    def write_register(self, address: int, value: int, slave: int):
        rr = None
        try:
            rr = self.client.write_register(address=address, value=value, slave=slave)
        except Exception as e:
            if slave in self.channels:
                self.channels.remove(slave)
            raise(e)
        else:
            if slave not in self.channels:
                self.channels.append(slave)
        return rr

    @check_connect
    @critical_section
    def write_registers(self, address: int, values: list, slave: int, no_response_expected=False):
        rr = None
        try:
            rr = self.client.write_registers(
                address=address, values=values, slave=slave, no_response_expected=no_response_expected)
        except Exception as e:
            if slave in self.channels:
                self.channels.remove(slave)
            raise(e)
        else:
            if slave not in self.channels:
                self.channels.append(slave)
        return rr
        
    @check_connect
    @critical_section
    def write_coil(self, address: int, value: int, slave: int):
        rr = None
        try:
            rr = self.client.write_coil(address=address, value=value, slave=slave)
        except Exception as e:
            if slave in self.channels:
                self.channels.remove(slave)
            raise(e)
        else:
            if slave not in self.channels:
                self.channels.append(slave)
        return rr
    
    def convert_from_registers(self, registers: list, data_type):
        return self.client.convert_from_registers(registers, data_type)

    def convert_to_registers(self, data: str, data_type):
        return self.client.convert_to_registers(data, data_type)

