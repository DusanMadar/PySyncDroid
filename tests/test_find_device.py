"""Tests for device finding functionality"""


from mock import patch

import pytest

from pysyncdroid.exceptions import DeviceException
from pysyncdroid.find_device import get_connection_details, get_mtp_details


@pytest.fixture()
def get_device():
    """
    Fixture - get details for a 'Linux Foundation 2.0/3.0 root hub' device.
    """
    return get_connection_details(vendor='linux', model='root')


def test_get_connection_details_device_exception():
    """
    Test get_connection_details raises a DeviceException with an appropriate
    message when trying to find a non-existent device.
    """
    with pytest.raises(DeviceException) as exc:
        get_connection_details(vendor='non-existent-vendor',
                               model='non-existent-model')

    exc_msg_parts = (
        'Device "non-existent-vendor non-existent-model" not found.',
        'No "non-existent-vendor" devices were found.',
    )

    assert str(exc.value) == '\n'.join(exc_msg_parts)


def test_get_connection_details_device_exception_message():
    """
    Test get_connection_details raises a DeviceException and the provided
    message lists all vendor devices when trying to find a non-existent model.
    """
    with pytest.raises(DeviceException) as exc:
        get_connection_details(vendor='linux', model='non-existent-model')

    exc_msg_parts = (
        'Device "linux non-existent-model" not found.',
        'Following "linux" devices were found:',
        'Linux Foundation 2.0 root hub',
        'Linux Foundation 3.0 root hub',
    )

    assert str(exc.value) == '\n'.join(exc_msg_parts)


def test_get_connection_details_expected_device(get_device):
    """
    Test get_connection_details returns usb_bus and device numbers for a
    given existing device.
    """
    assert get_device
    assert isinstance(get_device, tuple)


@patch('pysyncdroid.find_device.run_bash_cmd')
def test_get_connection_details_multiple_devices(mock_run_bash_cmd):
    """
    Test get_connection_details is able to find the given device in case of
    multiple devices from the same vendor (i.e. it doesn't pick up the first
    device for a certain vendor).
    """
    mocked_lsub_result = [
        'Bus 002 Device 001: ID 0123:0001 test_vendor test_model1',
        'Bus 002 Device 002: ID 0456:0002 test_vendor test_model2',
        'Bus 002 Device 003: ID 0789:0003 test_vendor test_model3'
    ]
    mock_run_bash_cmd.return_value = '\n'.join(mocked_lsub_result)
    usb_bus_id, device_id = get_connection_details(vendor='test_vendor',
                                                   model='test_model3')

    assert usb_bus_id == '002'
    assert device_id == '003'


def test_get_mtp_details(get_device):
    """
    Test get_mtp_details returns a valid path for a given device.
    """
    usb_bus, device = get_device

    mtp_details = get_mtp_details(usb_bus, device)
    assert isinstance(mtp_details, tuple)

    for mtp_detail in mtp_details:
        assert device in mtp_detail
        assert usb_bus in mtp_detail
