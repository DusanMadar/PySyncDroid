"""Find devices connected via MTP over USB"""


import os
import re

from pysyncdorid.utils import run_bash_cmd
from pysyncdorid.exceptions import DeviceException


#:
# pattern to find MTP connected devices
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
    vendor_pattern = re.compile(vendor, re.IGNORECASE)
    model_pattern = re.compile(model, re.IGNORECASE)

    usb_devices = run_bash_cmd(['lsusb'])

    # TODO: this assumes there is only one such device connected
    for device_info in usb_devices.split('\n'):
        if vendor_pattern.search(device_info) is None:
            continue

        if model_pattern.search(device_info) is None:
            continue

        bus = device_info[4:7]
        device = device_info[15:18]

        return bus, device

    else:
        exc_msg = 'Device "{v} {m}" not found'.format(v=vendor, m=model)
        raise DeviceException(exc_msg)


def get_mtp_path(usb_bus, device):
    """
    Get path to the device connected via MTP.

    :argument usb_bus: USB bus number
    :type usb_bus: str
    :argument device: device number
    :type interface: str

    :returns str

    """
    return MTP_PATH_PATTERN.format(u=os.getuid(), b=usb_bus, d=device)
