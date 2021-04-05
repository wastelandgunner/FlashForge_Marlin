#!/usr/bin/env python3

'''
Original script by: https://gist.github.com/zerog2k

Usage:  ./ff_flash_firmware.py /path/to/firmware.bin
'''

import hashlib
import sys
from time import sleep
import usb


def to_string(byt):
  return ''.join([chr(x) for x in byt])


FLASHFORGE_VENDOR_ID = 0x0315
CONTROL_EP = 0x01
FILE_EP = 0x03
MAX_WAIT_TIME = 0.5  # 500 milliseconds
RETRY_COUNT = 20
TARGET_FIRMWARE_NAME = "firmware.bin"

if len(sys.argv) < 1:
  raise ValueError('expecting firmware file: usage: ./ff_flash_firmware.py '
                   '/path/to/firmware.bin')

firmware = sys.argv[1]

# calculate checksum of the firmware
m = hashlib.md5()
fw = open(firmware, 'rb')
m.update(fw.read())
firmware_checksum = m.hexdigest()
firmware_size = fw.tell()
fw.seek(0)

print('Flashing firmware: ', firmware)
print('Searching for Flashforge printers ...')

retry = 1
while True:

    if retry >= RETRY_COUNT:
        raise ValueError('Did not find Flashforge compatible printers, '
                         'try again?')

    printer = usb.core.find(idVendor=FLASHFORGE_VENDOR_ID)

    if printer is None:
        retry = retry+1
    else:
        print('Found printer:\n\n', printer)
        break

    sleep(MAX_WAIT_TIME)

printer.set_configuration()

# add a bit delay to reduce timeouts
sleep(5)

# start control
printer.write(CONTROL_EP, '~M601 S0\r\n')
ret = printer.read(0x81, 5000)

print(to_string(ret.tobytes()))

# start fw write
fw_write_str = "~M28 {} 0:/sys/{}\r\n".format(firmware_size, TARGET_FIRMWARE_NAME)
printer.write(CONTROL_EP, fw_write_str)
ret = printer.read(0x81, 1000)
print(to_string(ret.tobytes()))
ret = printer.read(0x81, 1000)
print(to_string(ret.tobytes()))

# write fw to endpoint
printer.write(FILE_EP, fw.read(),
              5000)  # seems like i was getting timeouts below about 1500ms

# finish fw write
fw_write_str = "~M29 {}\r\n".format(firmware_checksum)
printer.write(CONTROL_EP, fw_write_str)
ret = printer.read(0x81, 1000)
print(to_string(ret.tobytes()))
ret = printer.read(0x81, 1000)
print(to_string(ret.tobytes()))

# trigger fw flash on next boot?
printer.write(CONTROL_EP, '~M600\r\n')
ret = printer.read(0x81, 1000)
print(to_string(ret.tobytes()))
ret = printer.read(0x81, 1000)
print(to_string(ret.tobytes()))

# stop control
printer.write(CONTROL_EP, '~M602\r\n')
ret = printer.read(0x81, 1000)
print(to_string(ret.tobytes()))
ret = printer.read(0x81, 1000)
print(to_string(ret.tobytes()))
