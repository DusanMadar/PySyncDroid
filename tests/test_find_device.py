"""Tests for device finding functionality"""


import pytest

from pysyncdroid.exceptions import DeviceException
from pysyncdroid.find_device import get_connection_details, get_mtp_details


@pytest.fixture
def get_device():
    """
    Fixture - get details for a 'Linux Foundation 2.0 root hub' device.
    """
    return get_connection_details(vendor='linux', model='root')


def test_get_connection_details_device_exception():
    """
    Test if get_connection_details raises a DeviceException when trying to find
    a non-existent device.
    """
    with pytest.raises(DeviceException):
        get_connection_details(vendor='vendor', model='model')


def test_get_connection_details_expected_device(get_device):
    """
    Test if get_connection_details returns usb_bus and device numbers for a
    given, existing device.
    """
    assert get_device
    assert isinstance(get_device, tuple)


def test_get_mtp_details(get_device):
    """
    Test if get_mtp_details returns a valid path for a given device.
    """
    usb_bus, device = get_device

    mtp_details = get_mtp_details(usb_bus, device)
    assert isinstance(mtp_details, tuple)

    for mtp_detail in mtp_details:
        assert device in mtp_detail
        assert usb_bus in mtp_detail
