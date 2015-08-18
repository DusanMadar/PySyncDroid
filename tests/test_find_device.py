"""Tests for device finding functionality"""


import pytest

from pysyncdroid.exceptions import DeviceException
from pysyncdroid.find_device import connection_details, get_mtp_path


@pytest.fixture
def get_device():
    """
    Fixture - get details for a 'Linux Foundation 2.0 root hub' device.
    """
    return connection_details(vendor='linux', model='root')


def test_connection_details_device_exception():
    """
    Test if connection_details raises a DeviceException when trying to find a
    non-existent device.
    """
    with pytest.raises(DeviceException):
        connection_details(vendor='vendor', model='model')


def test_connection_details_expected_device(get_device):
    """
    Test if connection_details returns usb_bus and device numbers for a given,
    existing device.
    """
    assert get_device
    assert isinstance(get_device, tuple)


def test_get_mtp_path(get_device):
    """
    Test if get_mtp_path returns a valid path for a given device.
    """
    usb_bus, device = get_device
    mtp = get_mtp_path(usb_bus, device)

    assert device in mtp
    assert usb_bus in mtp
