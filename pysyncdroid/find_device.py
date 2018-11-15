"""Find devices connected via MTP over USB"""


import os
import re

from pysyncdroid.exceptions import DeviceException
from pysyncdroid.utils import run_bash_cmd


# pattern to locate MTP connected devices via URL
# b - USB bus ID
# d - device ID
MTP_URL_PATTERN = "mtp://[usb:{b},{d}]/"


# pattern to locate MTP connected devices via gvfs
# u - user ID
# b - USB bus ID
# d - device ID
MTP_GVFS_PATH_PATTERN = "/run/user/{u}/gvfs/mtp:host=%5Busb%3A{b}%2C{d}%5D"


def lsusb():
    """
    A wrapper for the Linux `lsusb` commmand.
    """
    return run_bash_cmd(["lsusb"])


def get_connection_details(vendor, model):
    """
    Get device connection details (USB bus & device IDs).

    :argument vendor: device vendor name
    :type vendor: str
    :argument model: device model number
    :type model: str

    :returns tuple

    """
    vendor_devices = []

    vendor_pattern = re.compile(vendor, re.IGNORECASE)
    model_pattern = re.compile(model, re.IGNORECASE)

    # TODO: this assumes there is only one `vendor:model` device connected
    for device_info in lsusb().split("\n"):
        if vendor_pattern.search(device_info) is None:
            continue
        else:
            # collect only the human readable device info (i.e. ignore IDs)
            device_info_human = device_info[33:]
            if device_info_human not in vendor_devices:
                vendor_devices.append(device_info_human)

        if model_pattern.search(device_info) is None:
            continue

        # yep, USB bus ID and device ID are between these indexes
        usb_bus_id = device_info[4:7]
        device_id = device_info[15:18]

        return usb_bus_id, device_id

    # exception message base
    exc_msg = 'Device "{v} {m}" not found.\n'.format(v=vendor, m=model)

    # exception message extension base
    ext_base = '"{v}" devices were found'.format(v=vendor)

    if vendor_devices:
        exc_msg += "Following {b}:\n{d}".format(
            b=ext_base, d="\n".join(vendor_devices)
        )
    else:
        exc_msg += "No {b}.".format(b=ext_base)

    raise DeviceException(exc_msg)


def get_mtp_details(usb_bus_id, device_id):
    """
    Get MTP URL and gvfs path to the device.

    :argument usb_bus_id: USB bus ID
    :type usb_bus_id: str
    :argument device_id: device ID
    :type device_id: str

    :returns tuple

    """
    mtp_url = MTP_URL_PATTERN.format(b=usb_bus_id, d=device_id)
    mtp_gvfs_path = MTP_GVFS_PATH_PATTERN.format(
        u=os.getuid(), b=usb_bus_id, d=device_id
    )

    return mtp_url, mtp_gvfs_path
