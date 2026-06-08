
from typing import Optional

from devices import DeviceChannel

class FEBChannel:
    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        self._device: Optional[DeviceChannel] = None

    def attach(self, device: DeviceChannel):
        if device.channel_id != self.channel_id:
            raise ValueError(
                f"device channel {device.channel_id} "
                f"does not match FEB channel {self.channel_id}"
            )

        self._device = device

    @property
    def device(self) -> DeviceChannel:
        if self._device is None:
            raise RuntimeError(f"No device attached to channel {self.channel_id}")

        return self._device

    @property
    def type(self):
        return (None if self._device is None else type(self._device))

    def is_configured(self) -> bool:
        return self._device is not None
