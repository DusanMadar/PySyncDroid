"""Tests for sync functionality"""


import pytest

from pysyncdorid.sync import Sync

from pysyncdorid.exceptions import DeviceException
from pysyncdorid.find_device import connection_details, get_mtp_path


#: Constants
# computer constants
COMPUTER_SOURCE = '/home/dm/Music'
COMPUTER_SOURCE_FILE = '/home/dm/.bashrc'
COMPUTER_SOURCE_RELATIVE = 'Music/'
COMPUTER_SOURCE_EXPAND = '~/Music'

# testing device constants
VENDOR = 'samsung'
MODEL = 'gt-i9300'
DEVICE_SOURCE = 'Card/Music'
FAKE_DEVICE_SOURCE = 'CCard/Music'

# error messages
NOT_EXISTS = 'does not exists on computer neither on device'
NOT_DIRECTORY = 'is not a directory'


def no_device():
    """
    Helper - check if testing device is not connected

    :returns bool

    """
    no_device = False

    try:
        connection_details(vendor=VENDOR, model=MODEL)
    except DeviceException:
        no_device = True
    finally:
        return no_device


@pytest.fixture
def mtp():
    """
    Fixture - get MTP path to the testing device
    """
    usb_bus, device = connection_details(vendor=VENDOR, model=MODEL)
    mtp = get_mtp_path(usb_bus, device)

    return mtp


@pytest.mark.skipif(not no_device, reason="Testing device not connected")
def test_source_exists_device_ok(mtp):
    """
    Test if Sync is able to initialize; i.e. source exists and is a directory
    """
    Sync(mtp, DEVICE_SOURCE, '')


@pytest.mark.skipif(not no_device, reason="Testing device not connected")
def test_source_exists_device_fail(mtp):
    """
    Test if Sync is not able to initialize; i.e. source doesn't exists
    """
    with pytest.raises(OSError) as exc:
        Sync(mtp, FAKE_DEVICE_SOURCE, '')

    assert NOT_EXISTS in str(exc.value)


def test_source_exists_computer_ok(mtp):
    """
    Test if Sync is able to initialize; i.e. source exists and is a directory
    """
    Sync(mtp, COMPUTER_SOURCE, '')


def test_source_exists_computer_file(mtp):
    """
    Test if Sync is not able to initialize; i.e. source is a not a directory
    """
    with pytest.raises(OSError) as exc:
        Sync(mtp, COMPUTER_SOURCE_FILE, '')

    assert NOT_DIRECTORY in str(exc.value)


def test_source_exists_computer_relative(mtp):
    """
    Test if Sync is not able to initialize; i.e. source doesn't exists
    """
    with pytest.raises(OSError) as exc:
        Sync(mtp, COMPUTER_SOURCE_RELATIVE, '')

    assert NOT_EXISTS in str(exc.value)


def test_source_exists_computer_expand(mtp):
    """
    Test if Sync is not able to initialize; i.e. source doesn't exists
    """
    with pytest.raises(OSError) as exc:
        Sync(mtp, COMPUTER_SOURCE_EXPAND, '')

    assert NOT_EXISTS in str(exc.value)


# TODO: add test where device is the source
