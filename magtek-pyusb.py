#!/usr/bin/python3
"""
Read a MagTek USB HID Swipe Reader in Linux. A description of this
code can be found at: 
https://web.archive.org/web/20150829185405/http://www.micahcarrick.com/credit-card-reader-pyusb.html

Copyright (c) 2010 - Micah Carrick (original ver)
Copyright (c) 2024 - eadmaster (py3 + flipper0 output rewrite)
"""
import sys
import usb.core
import usb.util

VENDOR_ID = 0x0801
PRODUCT_ID = 0x0002
DATA_SIZE = 337

DEBUG = False

# find the MagTek reader

device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if device is None:
    sys.exit("Could not find MagTek USB HID Swipe Reader.")

# make sure the hiddev kernel driver is not active

if device.is_kernel_driver_active(0):
    try:
        device.detach_kernel_driver(0)
    except usb.core.USBError as e:
        sys.exit("Could not detatch kernel driver: %s" % str(e))

# set configuration

try:
    device.reset()
    device.set_configuration()
except usb.core.USBError as e:
    sys.exit("Could not set configuration: %s" % str(e))
    
endpoint = device[0][(0,0)][0]

# wait for swipe

data = []
swiped = False
sys.stderr.write("Please swipe your card...\n")

while 1:
    try:
        data += device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
        if not swiped: 
            sys.stderr.write("Reading...\n")
        swiped = True
        #print(data)
        if len(data) == DATA_SIZE:
            break
            
    except usb.core.USBError as e:
        if e.args == ('Operation timed out',) and swiped:
            if len(data) < DATA_SIZE:
                sys.stderr.write("Bad swipe, try again. (%d bytes)\n" % len(data))
                sys.stderr.write("Data: %s\n" % ''.join(map(chr, data)))
                data = []
                swiped = False
                continue
            else:
                break   # we got it!



# TODO: check data header == 0s -> read erorr
# else

# now we have the binary data from the MagReader! 


if DEBUG:
    enc_formats = ('ISO/ABA', 'AAMVA', 'CADL', 'Blank', 'Other', 'Undetermined', 'None')
    print("Card Encoding Type: %s" % enc_formats[data[6]])

    print("Track 1 Decode Status: %r" % bool(not data[0]))
    print("Track 1 Data Length: %d bytes" % data[3])
    print("Track 1 Data: %s" % ''.join(map(chr, data[7:116])))

    print("Track 2 Decode Status: %r" % bool(not data[1]))
    print("Track 2 Data Length: %d bytes" % data[4])
    print("Track 2 Data: %s" % ''.join(map(chr, data[117:226])))

    print("Track 3 Decode Status: %r" % bool(not data[2]))
    print("Track 3 Data Length: %d bytes" % data[5])
    print("Track 3 Data: %s" % ''.join(map(chr, data[227:336])))

    # since this is a bank card we can parse out the cardholder data

    #track = ''.join(map(chr, data[7:116]))
    #info = {}
    #i = track.find('^', 1)
    #info['account_number'] = track[2:i].strip()
    #j = track.find('/', i)
    #info['last_name'] = track[i+1:j].strip()
    #k = track.find('^', j)
    #info['first_name'] = track[j+1:k].strip()
    #info['exp_year'] = track[k+1:k+3]
    #info['exp_month'] = track[k+3:k+5]
    #print("Bank card info: ", info)


track1_data_str = ''.join(map(chr, data[7:116]))
track2_data_str = ''.join(map(chr, data[117:226]))
track3_data_str = ''.join(map(chr, data[227:336]))

# https://github.com/arha/magspoof_flipper/blob/main/assets/

print("Filetype: Flipper Mag device")
print("Version: 1")
print("# Mag device track data")
print("Track 1: " + track1_data_str)
print("Track 2: " + track2_data_str)
print("Track 3: " + track3_data_str)
