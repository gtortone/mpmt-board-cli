import sys
import mmap
from mini_rpc import rpc_service, rpc_method

@rpc_service()
class FPGA:

    def __init__(self, uiodev):
        try:
            self.fid = open(uiodev, 'r+b', 0)
        except FileNotFoundError:
            self.perror("UIO device not found") 
            sys.exit(-1)
        self.regs = mmap.mmap(self.fid.fileno(), 0x10000) 

    @rpc_method
    def readRegister(self, address:int):
        return int.from_bytes(self.regs[address*4:(address*4)+4], byteorder='little')

    @rpc_method
    def writeRegister(self, address:int, value:int):
        self.regs[address*4:(address*4)+4] = int.to_bytes(value, 4, byteorder='little') 
