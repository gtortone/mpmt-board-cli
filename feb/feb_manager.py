import inspect
import threading
import time
from feb.feb_channel import FEBChannel
from feb.modbus_manager import ModbusManager, ModbusConfig
from feb.devices import DeviceType, DeviceConfig
from feb.pmtchannel import PMTChannel
from feb.ledchannel import LEDChannel
from runcontrol.fpga import FPGA
from mini_rpc import rpc_service, rpc_method

@rpc_service()
class FEBManager:
    def __init__(self, cfg: ModbusConfig, maxChannels=19, config_from_fpga=True):
        self.modbus = ModbusManager(cfg)
        self.maxChannels = maxChannels
        self.fpga = FPGA('/dev/uio0')

        # channels are labeled from J1 to J19 (1...19)
        self._channels = [ FEBChannel(i) for i in range(maxChannels+1) ]

        # register 103 bit (x) is '1' for PMT channel, '0' for LED channel
        if config_from_fpga:
            pmtmask = self.fpga.readRegister(103)
            for ch in range(maxChannels):       # 0...18
                if pmtmask & 1<<ch:
                    self.configure(DeviceType.PMT, ch+1, ch+1)
                else:
                    self.configure(DeviceType.LED, ch+1, ch+21)

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self.probe_task)
        self._thread.start()

    def close(self):
        if not self._stop_event.is_set():
            self._stop_event.set()

            if self._thread.is_alive():
                self._thread.join(timeout=5)

    def probe_task(self):
        while True:
            for ch in self.getChannels():
                self.channel(ch).device.probe()
                if self._stop_event.is_set():
                    return
                time.sleep(0.250) 

    def channel(self, i: int) -> FEBChannel: 
        if i <= 0 or i>len(self._channels)-1:
            raise IndexError(f"Invalid channel index {i}")

        return self._channels[i]

    def clear(self):
        for i in range(self.maxChannels+1):
            self.channel(i).detach()

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
                report[str(ch)] = { 
                    "type": self.channel(ch).device.DEVICE_TYPE,
                    **self.channel(ch).device.readMonRegisters()
                }
            except Exception as e:
                ...
        return report

    @rpc_method
    # enable (turn-on) single channel
    def enableChannel(self, channel: int):
        if channel > self.maxChannels:
            raise IndexError(f"Invalid channel index {channel}")
        else: 
            mask = (1<<(channel-1))
            value = self.fpga.readRegister(1) | mask
            self.fpga.writeRegister(1, value)

    @rpc_method
    # disable (turn-off) single channel
    def disableChannel(self, channel: int):
        if channel > self.maxChannels:
            raise IndexError(f"Invalid channel index {channel}")
        else: 
            mask = (1<<(channel-1))
            value = self.fpga.readRegister(1) & ~mask
            self.fpga.writeRegister(1, value)
    
    @rpc_method
    # enable (turn-on) channels using list
    def enableChannels(self, channels: list[int]):
        for ch in channels:
            self.enableChannel(ch)

    @rpc_method
    # disable (turn-off) channels using list
    def disableChannels(self, channels: list[int]):
        for ch in channels:
            self.disableChannel(ch)

    @rpc_method
    # enable (turn-on) channels using bitmask
    def enableChannelsByMask(self, mask: int):
        for ch in range (0, self.maxChannels):
            if mask & (1<<ch):
                self.enableChannel(ch+1)

    @rpc_method
    # disable (turn-off) channels using bitmask
    def disableChannelsByMask(self, mask: int):
        for ch in range (0, self.maxChannels):
            if mask & (1<<ch):
                self.disableChannel(ch+1)

