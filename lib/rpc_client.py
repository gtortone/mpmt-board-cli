import httpx

class BaseClient:
    def __init__(self, url):
        self.url = url
        self._id = 0
        self.client = httpx.Client(base_url=url)

    def _call(self, method, params):
       self._id += 1
       resp = self.client.post(self.url, json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._id
       })
       data = resp.json()
       if 'error' in data and data['error']:
           raise Exception(data['error'])
       return data.get('result')

class HvCore:
    def __init__(self, client):
        self._client = client

    def getAlarm(self, slave):
        return self._client._call('hv.core.getAlarm', {"slave": slave})

    def getChannels(self):
        return self._client._call('hv.core.getChannels', {})

    def getCurrent(self, slave):
        return self._client._call('hv.core.getCurrent', {"slave": slave})

    def getInfo(self, slave):
        return self._client._call('hv.core.getInfo', {"slave": slave})

    def getRateRampdown(self, slave):
        return self._client._call('hv.core.getRateRampdown', {"slave": slave})

    def getRateRampup(self, slave):
        return self._client._call('hv.core.getRateRampup', {"slave": slave})

    def getStatus(self, slave):
        return self._client._call('hv.core.getStatus', {"slave": slave})

    def getTemperature(self, slave):
        return self._client._call('hv.core.getTemperature', {"slave": slave})

    def getThreshold(self, slave):
        return self._client._call('hv.core.getThreshold', {"slave": slave})

    def getVoltage(self, slave):
        return self._client._call('hv.core.getVoltage', {"slave": slave})

    def getVoltageSet(self, slave):
        return self._client._call('hv.core.getVoltageSet', {"slave": slave})

    def getVref(self, slave):
        return self._client._call('hv.core.getVref', {"slave": slave})

    def open(self, addr):
        return self._client._call('hv.core.open', {"addr": addr})

    def powerOff(self, slave):
        return self._client._call('hv.core.powerOff', {"slave": slave})

    def powerOn(self, slave):
        return self._client._call('hv.core.powerOn', {"slave": slave})

    def readCalibRegisters(self, slave):
        return self._client._call('hv.core.readCalibRegisters', {"slave": slave})

    def readMonRegisters(self, slave):
        return self._client._call('hv.core.readMonRegisters', {"slave": slave})

    def reset(self, slave):
        return self._client._call('hv.core.reset', {"slave": slave})

    def setFEBSerialNumber(self, sn, slave):
        return self._client._call('hv.core.setFEBSerialNumber', {"sn": sn, "slave": slave})

    def setHVSerialNumber(self, sn, slave):
        return self._client._call('hv.core.setHVSerialNumber', {"sn": sn, "slave": slave})

    def setLimitCurrent(self, value, slave):
        return self._client._call('hv.core.setLimitCurrent', {"value": value, "slave": slave})

    def setLimitTemperature(self, value, slave):
        return self._client._call('hv.core.setLimitTemperature', {"value": value, "slave": slave})

    def setLimitTriptime(self, value, slave):
        return self._client._call('hv.core.setLimitTriptime', {"value": value, "slave": slave})

    def setLimitVoltage(self, value, slave):
        return self._client._call('hv.core.setLimitVoltage', {"value": value, "slave": slave})

    def setModbusAddress(self, addr):
        return self._client._call('hv.core.setModbusAddress', {"addr": addr})

    def setPMTSerialNumber(self, sn, slave):
        return self._client._call('hv.core.setPMTSerialNumber', {"sn": sn, "slave": slave})

    def setRateRampdown(self, value, slave):
        return self._client._call('hv.core.setRateRampdown', {"value": value, "slave": slave})

    def setRateRampup(self, value, slave):
        return self._client._call('hv.core.setRateRampup', {"value": value, "slave": slave})

    def setThreshold(self, value, slave):
        return self._client._call('hv.core.setThreshold', {"value": value, "slave": slave})

    def setVoltageSet(self, value, slave):
        return self._client._call('hv.core.setVoltageSet', {"value": value, "slave": slave})

    def writeCalibDiscr(self, discr, slave):
        return self._client._call('hv.core.writeCalibDiscr', {"discr": discr, "slave": slave})

    def writeCalibOffset(self, offset, slave):
        return self._client._call('hv.core.writeCalibOffset', {"offset": offset, "slave": slave})

    def writeCalibSlope(self, slope, slave):
        return self._client._call('hv.core.writeCalibSlope', {"slope": slope, "slave": slave})

class FpgaCore:
    def __init__(self, client):
        self._client = client

    def readRegister(self, address):
        return self._client._call('fpga.core.readRegister', {"address": address})

    def writeRegister(self, address, value):
        return self._client._call('fpga.core.writeRegister', {"address": address, "value": value})

class HkCore:
    def __init__(self, client):
        self._client = client

    def read(self):
        return self._client._call('hk.core.read', {})

class HvComposite:
    def __init__(self, client):
        self._client = client

    def getChannels(self):
        return self._client._call('hv.composite.getChannels', {})

    def getStatus(self):
        return self._client._call('hv.composite.getStatus', {})

class RPCClient(BaseClient):
    def __init__(self, url):
        super().__init__(url)

        self.HvCore = HvCore(self)
        self.FpgaCore = FpgaCore(self)
        self.HkCore = HkCore(self)
        self.HvComposite = HvComposite(self)
