
from dataclasses import dataclass
from typing import Callable
from smbus2 import SMBus

from sensors.tla2024 import TLA2024
from sensors.bme280 import BME280
from sensors.lsm303 import LSM303Accel, LSM303Magnet

from mini_rpc import rpc_service, rpc_method

@dataclass
class SensorInfo:
    name: str
    address: int
    instance: object

@dataclass
class MetricInfo:
    label: str
    unit: str
    value: float
    multiplier: float
    divider: float
    width: int

@dataclass
class MetricOperation:
    label: str
    unit: str
    value: float
    index1: int
    index2: int
    op: Callable[[float, float], float] 
    width: int

DEVICE_MAP = {
    0x48: TLA2024,
    0x76: BME280,
    0x19: LSM303Accel,
    0x1E: LSM303Magnet,
    #0x88: BME280,       # test
}

ALIAS_MAP = {
    0x48: "tla2024",
    0x76: "bme280-in",
    0x19: "lsm303-acc",
    0x1E: "lsm303-mag",
    #0x88: "bme280-ext", 
}

METRIC_MAP = {
    0x48: [
        MetricInfo(label="+5.0V", unit="V", value=0, multiplier=3, divider=1000, width=5),
        MetricInfo(label="IpoeA", unit="A", value=0, multiplier=1, divider=1000, width=5),
        MetricInfo(label="+3.3V", unit="V", value=0, multiplier=2, divider=1000, width=5),
        MetricInfo(label="IpoeB", unit="A", value=0, multiplier=1, divider=1000, width=5),
    ],
    0x76: [
        MetricInfo(label="T", unit="°C", value=0, multiplier=1, divider=1, width=6), 
        MetricInfo(label="P", unit="hPa", value=0, multiplier=1, divider=1, width=7),
        MetricInfo(label="H", unit="%Rh", value=0, multiplier=1, divider=1, width=6) 
    ],
    0x19: [
        MetricInfo(label="X", unit="g", value=0, multiplier=1, divider=1, width=7), 
        MetricInfo(label="Y", unit="g", value=0, multiplier=1, divider=1, width=7),
        MetricInfo(label="Z", unit="g", value=0, multiplier=1, divider=1, width=7) 
    ],
    0x1E: [
        MetricInfo(label="X", unit="µT", value=0, multiplier=1, divider=1, width=6), 
        MetricInfo(label="Y", unit="µT", value=0, multiplier=1, divider=1, width=6),
        MetricInfo(label="Z", unit="µT", value=0, multiplier=1, divider=1, width=6) 
    ],
}

OPERATION_MAP = {
    0x48: [
        MetricOperation(label="PpoeA", unit="W", value=0, index1=0, index2=1, op=lambda a,b: a * b, width=5),
        MetricOperation(label="PpoeB", unit="W", value=0, index1=2, index2=3, op=lambda a,b: a * b, width=5),
    ],
}

I2C_BUS = 1

@rpc_service()
class HouseKeeping:

    def __init__(self):
        self.sensors = []
        self.readings = {}
        self.discovery()
        #print(self.sensors)

    def discovery(self):
        bus = SMBus(I2C_BUS)
        self.sensors = []

        for address, sensor_class in DEVICE_MAP.items():
            try:
                bus.read_byte(address)
            except OSError:
                continue

            sensor = sensor_class(I2C_BUS, address)
            self.sensors.append(SensorInfo(name=f"{ALIAS_MAP.get(address, '')}", address=address, instance=sensor))

    @rpc_method
    def read(self):
        for s in self.sensors:
            self.readings[s.name] = []
            data_conv = []
            data = s.instance.readAll()
            for i, value in enumerate(data):
                d = {}
                metric = METRIC_MAP[s.address][i]
                d["label"] = metric.label
                d["unit"] = metric.unit
                d["value"] = round((value * metric.multiplier) / metric.divider, 2)
                self.readings[s.name].append(d)
                data_conv.append(d["value"])

            if OPERATION_MAP.get(s.address, None):
                for operation in OPERATION_MAP[s.address]:
                    d = {}
                    d["label"] = operation.label
                    d["unit"] = operation.unit
                    d["value"] = round(operation.op(data_conv[operation.index1], data_conv[operation.index2]), 2)
                    self.readings[s.name].append(d)

        return self.readings

if __name__=="__main__":
    hk = HouseKeeping()
    import json
    print(json.dumps(hk.read()))
