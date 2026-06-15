
import inspect
from feb.devices import PMTChannel, LEDChannel
from feb.feb_channel import FEBChannel
from feb.modbus_manager import ModbusManager, ModbusConfig
from feb.devices import DeviceType
from mini_rpc import rpc_service, rpc_method

@rpc_service()
class FEBManager:
    def __init__(self, cfg: ModbusConfig, maxChannels=19):
        self.modbus = ModbusManager(cfg)
        self.maxChannels = maxChannels

        # channels are labeled from J1 to J19 (1...19)
        self._channels = [
            FEBChannel(i)
            for i in range(maxChannels+1)
        ]

    def channel(self, i: int) -> FEBChannel: 
        if i <= 0 or i>len(self._channels)-1:
            raise IndexError(f"Invalid channel index {i}")

        return self._channels[i]

    # parameters to attach a device on a FEB channel
    # channel: FEB channel number (1...19)
    # address: device Modbus address

    def configure(self, dtype: DeviceType, channel: int, address: int):
        if dtype == DeviceType.PMT:
            device = PMTChannel(self.modbus, channel, address)
        elif dtype == DeviceType.LED:
            device = LEDChannel(self.modbus, channel, address)
        else:
            raise ValueError(f"Invalid channel type: {dtype}")
        self.channel(channel).attach(device)

    @rpc_method
    def call(self, channel: int, method: str, params: dict):
        dev = self._channels[channel].device

        #if method_name.startswith("_"):
        #    raise ValueError("private method")

        mth = getattr(dev, method)

        sig = inspect.signature(mth)
        bound = sig.bind(**params)

        return mth(*bound.args, **bound.kwargs)

    def getChannels(self, dtype: DeviceType = None):
        if dtype is None:
            return [ch.channel for ch in self._channels if ch.is_configured()]
        else:
            return [ch.channel for ch in self._channels 
                if ch.is_configured() and ch.device.DEVICE_TYPE == dtype]

    def getOnlineChannels(self, dtype: DeviceType = None):
        probed_channels = self.modbus.getChannels()
        if dtype is None:
            return probed_channels
        else:
            return list(set(probed_channels) & set(self.getChannels(dtype)))

    def getOfflineChannels(self, dtype: DeviceType = None):
        return list(set(range(1, self.maxChannels)) ^ set(self.getOnlineChannels()))
