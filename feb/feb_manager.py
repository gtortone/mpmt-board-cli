
import inspect
from feb.feb_channel import FEBChannel
from feb.modbus_manager import ModbusManager, ModbusConfig
from feb.devices import DeviceType, DeviceConfig
from feb.pmtchannel import PMTChannel
from runcontrol.fpga import FPGA
from mini_rpc import rpc_service, rpc_method

@rpc_service()
class FEBManager:
    def __init__(self, cfg: ModbusConfig, maxChannels=19, config_from_fpga=True):
        self.modbus = ModbusManager(cfg)
        self.maxChannels = maxChannels
        fpga = FPGA('/dev/uio0')

        # channels are labeled from J1 to J19 (1...19)
        self._channels = [ FEBChannel(i) for i in range(maxChannels+1) ]

        # register 103 bit (x) is '1' for PMT channel, '0' for LED channel
        if config_from_fpga:
            pmtmask = fpga.readRegister(103)
            for ch in range(maxChannels):       # 0...18
                if pmtmask & 1<<ch:
                    self.configure(DeviceType.PMT, ch+1, ch+1)
                else:
                    self.configure(DeviceType.LED, ch+1, ch+21)

    def channel(self, i: int) -> FEBChannel: 
        if i <= 0 or i>len(self._channels)-1:
            raise IndexError(f"Invalid channel index {i}")

        return self._channels[i]

    def clear(self):
        for i in range(self.maxChannels+1):
            FEBChannel(i).detach()

    def setup(self, cfg: list[DeviceConfig]):
        self.clear()
        for dev in cfg:
            self.configure(dev.device_type, dev.channel, dev.address)

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
        dev = self.channel(channel).device

        mth = getattr(dev, method)

        sig = inspect.signature(mth)
        bound = sig.bind(**params)

        return mth(*bound.args, **bound.kwargs)

    @rpc_method
    # returns board channel numbers filtered by DeviceType or all 
    def getChannels(self, dtype: DeviceType = None):
        if dtype is None:
            return [ch.channel for ch in self._channels if ch.is_configured()]
        else:
            return [ch.channel for ch in self._channels 
                if ch.is_configured() and ch.device.DEVICE_TYPE == dtype]

    @rpc_method
    # returns online board channel numbers filtered by DeviceType or all 
    def getOnlineChannels(self, dtype: DeviceType = None):
        online_channels = []
        for ch in self.getChannels():
            if self.channel(ch).device.online:
                online_channels.append(self.channel(ch).device.channel) 
        if dtype is None:
            return online_channels
        else:
            return list(set(online_channels) & set(self.getChannels(dtype)))

    @rpc_method
    # returns offline board channel numbers filtered by DeviceType or all 
    def getOfflineChannels(self, dtype: DeviceType = None):
        offline_channels = []
        for ch in self.getChannels():
            if not self.channel(ch).device.online:
                offline_channels.append(self.channel(ch).device.channel) 
        if dtype is None:
            return offline_channels
        else:
            return list(set(offline_channels) & set(self.getChannels(dtype)))

    @rpc_method
    # return overall status for online channels
    def getStatus(self, dtype: DeviceType = None):
        report = {}
        for ch in self.getOnlineChannels(dtype):
            try:
                report[str(ch)] = self.channel(ch).device.readMonRegisters()
            except Exception as e:
                ...
        return report
