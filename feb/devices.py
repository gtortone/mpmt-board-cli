
import struct
from abc import ABC
from enum import Enum
from functools import wraps
from dataclasses import dataclass

# DeviceChannel is an abstract class
# implemented channels inherit from DeviceChannel
# and have 'modbus' instance to set/get parameters

class DeviceType(str, Enum):
    PMT = "PMT"
    LED = "LED"

@dataclass
class DeviceConfig:
    device_type: DeviceType
    channel: int
    address: int

class DeviceChannel(ABC):
    DEVICE_TYPE = None

    # decorators

    def validate_range(min_value, max_value):
        def decorator(func):
            @wraps(func)
            def wrapper(self, value, *args, **kwargs):
                if not min_value <= value <= max_value:
                    raise ValueError(f"{func.__name__}: value {value} out of range" f"[{min_value}, {max_value}]")
                return func(self, value, *args, **kwargs)
            return wrapper
        return decorator

    def track_connection(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                ret = func(self, *args, **kwargs)
            except Exception as e:
                self.online = False 
                raise(e)
            else:
                self.online = True
                return ret
        return wrapper

    def __init__(self, modbus, channel: int, address: int):
        self.modbus = modbus
        self.address = address      # modbus address
        self.channel = channel      # board channel address
        self.online = False         # true/false if read/write operation ok/fail

    # device derived class must provide probe implementation
    def probe(self):
        None

    def __str__(self):
        return (f"Board channel: {self.channel}, MB address: {self.address}, online: {self.online}")

