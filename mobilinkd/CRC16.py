'''
Created on Dec 3, 2020

@author: rob
'''

class CRC16(object):
    
    def __init__(self, poly, init):
        self.poly = poly
        self.init = init
        self.mask = 0xFFFF
        self.msb = 0x8000
        self.reset()
    
    def reset(self):
        self.reg = self.init
        for i in range(16):
            bit = self.reg & 0x01
            if bit:
                self.reg ^= self.poly
            self.reg >>= 1
            if bit:
                self.reg |= self.msb
        self.reg &= self.mask

    def crc(self, data):
        for byte in data:
            for i in range(8):
                msb = self.reg & self.msb
                self.reg = ((self.reg << 1) & self.mask) | ((byte >> (7 - i)) & 0x01)
                if msb:
                    self.reg ^= self.poly
         
    def get(self):
        reg = self.reg
        for i in range(16):
            msb = reg & self.msb
            reg = ((reg << 1) & self.mask)
            if msb:
                reg ^= self.poly

        return reg & self.mask
    
         
    def get_bytes(self):
        crc = self.get()
        return bytearray([(crc>>8) & 0xFF, crc & 0xFF])
        