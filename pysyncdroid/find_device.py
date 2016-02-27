"""Find devices connected via MTP over USB"""


import os
import re

from pysyncdroid.utils import run_bash_cmd
from pysyncdroid.exceptions import DeviceException


#:
# pattern to find MTP connected devices
# u - user ID
# b - USB bus ID
# d - device ID
MTP_PATH_PATTERN = '/run/user/{u}/gvfs/mtp:host=%5Busb%3A{b}%2C{d}%5D'


def connection_details(vendor, model):
    """
    Get device connection details (USB bus & device numbers).

    :argument vendor: device vendor name
    :type vendor: str
    :argument model: device model number
    :type model: str

    :returns tuple

    """
    vendor_devices = []

    vendor_pattern = re.compile(vendor, re.IGNORECASE)
    model_pattern = re.compile(model, re.IGNORECASE)

    usb_devices = run_bash_cmd(['lsusb'])

    # TODO: this assumes there is only one `vendor:model` device connected
    for device_info in usb_devices.split('\n'):
        if vendor_pattern.search(device_info) is None:
            continue
        else:
            # collect only the human readable device info (i.e. ignore IDs)
            vendor_devices.append(device_info[33:])

        if model_pattern.search(device_info) is None:
            continue

        # yep, USB bus ID and device ID are between these indexes
        usb_bus = device_info[4:7]
        device = device_info[15:18]

        return usb_bus, device

    else:
        # exception message base
        exc_msg = 'Device "{v} {m}" not found.\n'.format(v=vendor, m=model)

        # exception message extension base
        ext_base = '"{v}" devices were found'.format(v=vendor)

        if vendor_devices:
            exc_msg += ('Following {b}:\n{d}'
                        .format(b=ext_base, d='\n'.join(vendor_devices)))
        else:
            exc_msg += 'No {b}.'.format(b=ext_base)

        raise DeviceException(exc_msg)


def get_mtp_path(usb_bus, device):
    """
    Get path to the device connected via MTP.

    :argument usb_bus: USB bus ID
    :type usb_bus: str
    :argument device: device ID
    :type interface: str

    :returns str

    """
    return MTP_PATH_PATTERN.format(u=os.getuid(), b=usb_bus, d=device)
