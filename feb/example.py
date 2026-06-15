
from feb.devices import DeviceType
from feb.feb_manager import FEBManager
from feb.modbus_manager import ModbusConfig

mgr = FEBManager(ModbusConfig(mode="rtu", port="/dev/ttyPS1"))

pmt_channels = [2, 3, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18]
led_channels = [1, 4, 7, 10, 19]

for ch in pmt_channels:
    mgr.configure(DeviceType.PMT, channel=ch, address=ch)

for ch in led_channels:
    mgr.configure(DeviceType.LED, channel=ch, address=20+ch)

print(mgr.channel(2).type)
print(mgr.channel(7).type)

hv = mgr.channel(6).device
hv.setVoltageSet(1250)
# or
mgr.channel(6).device.setVoltageSet(1000)

#led = mgr.channel(7).device
#led.set_state(True)

print("- configured channels -")
print(mgr.getChannels())
print("- configured channels (PMT) -")
print(mgr.getChannels(DeviceType.PMT))
print("- configured channels (LED) -")
print(mgr.getChannels(DeviceType.LED))

print("- online channels -")
print(mgr.getOnlineChannels())
print("- offline channels -")
print(mgr.getOfflineChannels())
print("- online channels (PMT) -")
print(mgr.getOnlineChannels(DeviceType.PMT))
print("- online channels (LED) -")
print(mgr.getOnlineChannels(DeviceType.LED))

print("- get status CH#6 (PMT) -")
print(mgr.channel(6).device.readMonRegisters())
