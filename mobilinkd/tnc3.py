'''
Created on Dec 3, 2020

@author: rob
'''

from bluetooth import *
from mobilinkd.KissDecode import KissDecode
from mobilinkd.CRC16 import CRC16
import io, struct

class TNC3(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        # self.rfcomm_devices = find_service(uuid='00001101-0000-1000-8000-00805f9b34fb')
        self.device = None
        self.lsf_callback = None
        self.audio_callback = None
        self.decoder = KissDecode()
        self.crc = CRC16(0x5935, 0xFFFF)
        
    
    @staticmethod
    def decode_callsign_base40(encoded_bytes):

        # Convert byte array to integer value.
        i,h = struct.unpack(">HI", encoded_bytes)
        encoded = (i << 16) | h
        
        # Unpack each base-40 digit and map them to the appriate character.
        result = io.StringIO()
        while encoded:
            result.write("xABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/."[encoded % 40])
            encoded //= 40;
        
        return result.getvalue();


    def ok(self):
        return self.checksum == 0
    
    def callsign(self, packet):
        return self.decode_callsign_base40(packet[6:12])
        
    def open(self, mac):
        port = 6
        self.ser = None
        self.ser = BluetoothSocket(RFCOMM)
        # print(f"Connecting to {mac:}/{port:}", file=sys.stderr)
        self.ser.connect((mac, port))

    def run(self, lsf_callback, audio_callback):
        if self.ser is None:
            raise RuntimeError('device not opened')
        self.lsf_callback = lsf_callback
        self.audio_callback = audio_callback

        while True:
            block = bytes(self.ser.recv(12))
            if len(block) == 0: continue
            for c in block:
                packet = self.decoder.process(c)
                if packet is not None:
                    if not self.handle_packet(packet):
                        pass
         
    def handle_packet(self, packet):
        if packet.packet_type != 0x20: # Stream is from TNC id 2.
            print("unhandled packet type = %d" % packet.packet_type, file=sys.stderr)
            return False
        
        if len(packet.data) == 30:
            self.handle_lsf(packet.data)
            return True
        elif len(packet.data) == 26:
            return self.handle_audio(packet.data)
        else:
            print("unhandled, len = %d" % len(packet.data), file=sys.stderr)
        return False

    def handle_lsf(self, packet):
        self.crc.reset()
        self.crc.crc(packet)
        checksum = self.crc.get()
        if (checksum != 0): print(checksum, file=sys.stderr)
        self.lsf_callback(self.callsign(packet))
 
    def handle_audio(self, packet):
        self.crc.reset()
        self.crc.crc(packet[6:])
        checksum = self.crc.get()
        if (checksum != 0): print(checksum, file=sys.stderr)
        self.audio_callback(packet[8:24])
       
    