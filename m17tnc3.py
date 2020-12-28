#!/usr/bin/python3
# encoding: utf-8
'''
m17tnc3 -- m17/codec2 demodulator for Mobilinkd TNC3

m17tnc3 is a program for decoding M17 audio streams sent via KISS
from a Mobilinkd TNC3.

@author:     rob

@copyright:  2020 Mobilinkd LLC. All rights reserved.

@license:    Apache License 2.0

@contact:    rob@mobilinkd.com
@deffield    updated: 2020-12-03
'''

import sys
import os

import sounddevice as sd
import pycodec2
import struct
import numpy as np
import binascii
import queue

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from mobilinkd.tnc3 import TNC3

__all__ = []
__version__ = 0.1
__date__ = '2020-12-03'
__updated__ = '2020-12-03'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

q = queue.Queue(maxsize=1000)
streaming = False

def stream_callback(outdata, frames, time, status):
    global streaming
    
    if status.output_underflow:
        print('Output underflow: increase blocksize?', file=sys.stderr)
        raise sd.CallbackAbort
    assert not status

    if not streaming:
        outdata[:, 0] = np.zeros(len(outdata))
        if q.qsize() > 5:
            streaming = True
        return
    
    try:
        outdata[:, 0] = q.get_nowait()
    except queue.Empty as e:
        print('empty', file=sys.stderr)
        outdata[:, 0] = np.zeros(len(outdata))
        streaming = False

c2 = pycodec2.Codec2(3200)

def audio_callback(data):
    
    # decoded_audio = c2.decode(bytes(frame[3:11])) + c2.decode(bytes(frame[11:19]))
    # sys.stdout.buffer.write(decoded_audio.tobytes())
    # print(binascii.hexlify(decoded_audio))
    q.put_nowait(
        np.concatenate([
            c2.decode(bytes(data[:8])),
            c2.decode(bytes(data[8:]))
        ]))

def lsf_callback(callsign):
    print("receiving: ", callsign)

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by rob on %s.
  Copyright 2020 Mobilinkd LLC. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="mac", help="MAC address of the TNC3", metavar="mac", nargs='?')

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose

        tnc = TNC3()
        tnc.open(args.mac)
        stream = sd.OutputStream(
            samplerate=8000, blocksize=320, channels=1, dtype="int16",
            callback=stream_callback, latency='high')
        
        with stream:
            tnc.run(lsf_callback, audio_callback)
        
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
#     except Exception as e:
#         if DEBUG or TESTRUN:
#             raise(e)
#         indent = len(program_name) * " "
#         sys.stderr.write(program_name + ": " + repr(e) + "\n")
#         sys.stderr.write(indent + "  for help use --help")
#         return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
        sys.argv.append("-v")
        sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'm17tnc3_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())