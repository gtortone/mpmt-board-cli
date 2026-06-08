
from highvoltage.hvmodbus import HVModbus
from mini_rpc import rpc_service, rpc_method

@rpc_service()
class HVComposite:

    def __init__(self, hv: HVModbus):
        self.hv = hv
        self.channels = self.probe()

    def probe(self):
        output = []
        for addr in range(1,21):
            if self.hv.open(addr):
                output.append(addr)
        return output

    @rpc_method
    def getChannels(self):
        return self.channels

    @rpc_method
    def getStatus(self):
        output = []
        for addr in self.channels:
            output.append({
                "channel": addr, 
                "status": self.hv.getStatus(addr),
                "voltage": self.hv.getVoltage(addr),
                "current": self.hv.getCurrent(addr),
                "temperature": self.hv.getTemperature(addr)
            })
        return output
