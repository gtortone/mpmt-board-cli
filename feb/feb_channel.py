
from feb.devices import DeviceChannel
from enum import Enum

# FEBChannel contains attached DeviceChannel

class FEBChannel:
    def __init__(self, channel: int):
        self.channel = channel
        self._device: DeviceChannel = None

    def attach(self, device: DeviceChannel):
        self._device = device

    def detach(self):
        self._device = None

    @property
    def device(self) -> DeviceChannel:
        if self._device is None:
            raise RuntimeError(f"No device attached to channel {self.channel}")

        return self._device

    @property
    def type(self):
        return (None if self._device is None else self._device.DEVICE_TYPE)

    def is_configured(self) -> bool:
        return self._device is not None
