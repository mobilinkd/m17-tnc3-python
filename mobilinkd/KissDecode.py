'''
Created on Dec 3, 2020

@author: rob
'''

class KissData(object):

    def __init__(self):
        self.packet_type = None;
        self.sub_type = None;
        self.data = None
        self.ready = False;

class KissDecode(object):

    WAIT_FEND = 1
    WAIT_PACKET_TYPE = 2
    WAIT_SUB_TYPE = 3
    WAIT_DATA = 4

    FEND = 0xC0
    FESC = 0xDB
    TFEND = 0xDC
    TFESC = 0xDD

    def __init__(self):
        self.state = self.WAIT_FEND
        self.packet = KissData()
        self.escape = False
        self.parser = {
            self.WAIT_FEND: self.wait_fend,
            self.WAIT_PACKET_TYPE: self.wait_packet_type,
            self.WAIT_SUB_TYPE: self.wait_sub_type,
            self.WAIT_DATA: self.wait_data}
        self.tmp = bytearray()
    
    def process(self, c):
        if self.escape:
            if c == self.TFEND:
                c = self.FEND
            elif c == self.TFESC:
                c = self.FESC
            else:
                # Bogus sequence
                self.escape = False
                return None
        elif c == self.FESC:
            self.escape = True
            return None
            
        self.parser[self.state](c, self.escape)
        self.escape = False
        
        if self.packet is not None and self.packet.ready:
            return self.packet
        else:
            return None
    
    def wait_fend(self, c, escape):
    
        if c == self.FEND:
            self.state = self.WAIT_PACKET_TYPE
            self.packet = KissData()
            # print self.tmp
            self.tmp = bytearray()
        else:
            self.tmp.append(c)
    
    def wait_packet_type(self, c, escape):
        
        if not escape and c == self.FEND: return # possible dupe
        self.packet.packet_type = c
        if (c & 0x0F) == 0x06:
            self.state = self.WAIT_SUB_TYPE
        else:
            self.packet.data = bytearray()
            self.state = self.WAIT_DATA
    
    def wait_sub_type(self, c, escape):
        self.packet.sub_type = c
        self.packet.data = bytearray()
        self.state = self.WAIT_DATA
    
    def wait_data(self, c, escape):
        if not escape and c == self.FEND:
            self.packet.ready = True
            self.state = self.WAIT_FEND
        else:
            self.packet.data.append(c)
        