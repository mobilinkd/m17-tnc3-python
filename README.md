# m17-tnc3-python
Test app for interacting with the Mobilinkd TNC3 (and NucleoTNC) using M17 protocol over KISS.

## Prerequisites

 - pycodec2
 - sounddevice
 - numpy
 - bluetooth

## Usage

    $ ./m17tnc3.py <TNC3 MAC Address>
    
For example:

    $ ./m17tnc3.py 34:81:F4:3D:80:5E
    
The TNC3 must be running firmware version 2.1.1 or later.  This is highly
experimental and subject to massive changes.
