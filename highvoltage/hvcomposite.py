
from highvoltage.hvmodbus import HVModbus
from mini_rpc import rpc_service, rpc_method

@rpc_service()
class HVComposite:

    def __init__(self, hv: HVModbus):
        self.hv = hv

    @rpc_method
    def getStatus(self):
        output = []
        for addr in self.hv.getChannels():
            try:
                status = self.hv.getStatus(addr)
                voltage = self.hv.getVoltage(addr)
                current = self.hv.getCurrent(addr)
                temperature = self.hv.getTemperature(addr)
            except Exception as e:
                continue
            else:
                output.append({
                    "channel": addr, 
                    "status": self.hv.getStatus(addr),
                    "voltage": self.hv.getVoltage(addr),
                    "current": self.hv.getCurrent(addr),
                    "temperature": self.hv.getTemperature(addr)
                })
        return output
