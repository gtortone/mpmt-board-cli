
from feb.modbus_manager import ModbusConfig
from feb.feb_manager import FEBManager
from feb.devices import DeviceType, DeviceConfig
from feb.pmtchannel import PMTChannel
from feb.ledchannel import LEDChannel

########################
### FEBManager usage ###
########################

# auto config from FPGA register 103
mgr = FEBManager(ModbusConfig(mode="rtu", port="/dev/ttyPS1"))

# ----------------------------------------------------

# config with channel list

#channels = [
#    DeviceConfig(DeviceType.PMT, 1, 1),
#    DeviceConfig(DeviceType.PMT, 2, 2),
#    DeviceConfig(DeviceType.PMT, 3, 3),
#    DeviceConfig(DeviceType.PMT, 4, 4),
#    DeviceConfig(DeviceType.PMT, 5, 5),
#    DeviceConfig(DeviceType.PMT, 6, 6),
#    DeviceConfig(DeviceType.PMT, 7, 7),
#    DeviceConfig(DeviceType.PMT, 8, 8),
#    DeviceConfig(DeviceType.PMT, 9, 9),
#    DeviceConfig(DeviceType.PMT, 10, 10),
#    DeviceConfig(DeviceType.LED, 11, 11),
#    DeviceConfig(DeviceType.LED, 12, 12),
#]
# mgr.setup(channels)

# ----------------------------------------------------

# config single channel

#for ch in pmt_channels:
#    mgr.configure(DeviceType.PMT, channel=ch, address=ch)
#
#for ch in led_channels:
#    mgr.configure(DeviceType.LED, channel=ch, address=20+ch)

# ----------------------------------------------------

########################
### PMTChannel usage ###
########################

hv = mgr.channel(6).device
hv.setVoltageSet(1250)
## or
mgr.channel(6).device.setVoltageSet(1000)

##########################
### FEBManager helpers ###
##########################

# get added/configured board channels (all)

print("- configured channels -")
print(mgr.getChannels())

# get added/configured board channels (filtered)

print("- configured channels (PMT) -")
print(mgr.getChannels(DeviceType.PMT))
print(mgr.getChannels("PMT"))
print("- configured channels (LED) -")
print(mgr.getChannels(DeviceType.LED))

# get online/offline board channels (all)

print("- online channels -")
print(mgr.getOnlineChannels())
print("- offline channels -")
print(mgr.getOfflineChannels())

# get online/offline board channels (filtered)

print("- online channels (PMT) -")
print(mgr.getOnlineChannels(DeviceType.PMT))
print("- online channels (LED) -")
print(mgr.getOnlineChannels(DeviceType.LED))

# invoke PMTChannel method

print("- get status CH#6 (PMT) -")
print(mgr.channel(6).device.readMonRegisters())
