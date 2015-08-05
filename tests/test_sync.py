"""Tests for Sync functionality"""


import os
import pytest
import getpass

from pysyncdorid.sync import Sync

from pysyncdorid.exceptions import DeviceException
from pysyncdorid.find_device import connection_details, get_mtp_path


#: Constants
CURRENT_DIRECTORY = os.getcwd()
CURRENT_USER = getpass.getuser()

COMPUTER_HOME = '/home/{u}/'.format(u=CURRENT_USER)
COMPUTER_SOURCE = os.path.join(COMPUTER_HOME, 'Music')
COMPUTER_SOURCE_FILE = os.path.join(COMPUTER_HOME, '.bashrc')

DEVICE_VENDOR = 'samsung'
DEVICE_MODEL = 'gt-i9300'
DEVICE_SOURCE = 'Card/Music'
DEVICE_SOURCE_FAKE = 'CCard/Music'

DEVICE_NOT_CONNECTED = "Testing device not connected"

# expected exception messages
NOT_EXISTS = 'does not exists on computer neither on device'
NOT_DIRECTORY = 'is not a directory'


def device_not_connected():
    """
    Helper - check if testing device not connected

    :returns bool

    """
    try:
        connection_details(vendor=DEVICE_VENDOR, model=DEVICE_MODEL)
    except DeviceException:
        device_not_connected = True
    else:
        device_not_connected = False
    finally:
        return device_not_connected


@pytest.fixture
def mtp():
    """
    Fixture - get MTP path to the testing device

    :returns str

    """
    usb_bus, device = connection_details(vendor=DEVICE_VENDOR,
                                         model=DEVICE_MODEL)
    mtp = get_mtp_path(usb_bus, device)

    return mtp


@pytest.fixture
def cd_home():
    """
    Fixture - cd to '~'
    """
    os.chdir(COMPUTER_HOME)


@pytest.fixture
def cd_back(request):
    """
    Fixture - cd to '-', i.e. back to previous directory
    """
    def fin():
        os.chdir(CURRENT_DIRECTORY)

    request.addfinalizer(fin)


# device source tests ---------------------------------------------------------
# -----------------------------------------------------------------------------
@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_source_exists_on_device(mtp):
    """
    Test if Sync is able to initialize; i.e. source exists and is a directory
    """
    sync = Sync(mtp, DEVICE_SOURCE, '')
    assert sync.source == os.path.join(mtp, DEVICE_SOURCE)


@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_source_not_exists_on_device(mtp):
    """
    Test if Sync is not able to initialize; i.e. source doesn't exists
    """
    with pytest.raises(OSError) as exc:
        Sync(mtp, DEVICE_SOURCE_FAKE, '')

    assert NOT_EXISTS in str(exc.value)


# computer source tests -------------------------------------------------------
# -----------------------------------------------------------------------------
def test_source_exists_on_computer():
    """
    Test if Sync is able to initialize; i.e. source exists and is a directory
    """
    sync = Sync('', COMPUTER_SOURCE, '')
    assert sync.source == COMPUTER_SOURCE


def test_source_exists_on_computer_relative(cd_home, cd_back):
    """
    Test if Sync is able to initialize; i.e. source exists and is a directory
    even if is specified as a relative path which is OK in this context
    """
    music = 'Music/'

    sync = Sync('', music, '')
    assert sync.source == os.path.join(COMPUTER_HOME, music)


def test_source_not_exists_on_computer_relative():
    """
    Test if Sync is not able to initialize; i.e. source doesn't exists as it
    is specified as a relative path which is wrong in this context
    """
    with pytest.raises(OSError) as exc:
        Sync('', 'Music/', '')

    assert NOT_EXISTS in str(exc.value)


def test_source_not_exists_on_computer_expand():
    """
    Test if Sync is not able to initialize; i.e. source doesn't exists as the
    Sync class does not support expanding paths
    """
    with pytest.raises(OSError) as exc:
        Sync('', '~/Music', '')

    assert NOT_EXISTS in str(exc.value)


def test_source_is_a_file_on_computer():
    """
    Test if Sync is not able to initialize; i.e. source is a not a directory
    """
    with pytest.raises(OSError) as exc:
        Sync('', COMPUTER_SOURCE_FILE, '')

    assert NOT_DIRECTORY in str(exc.value)


# destination tests -----------------------------------------------------------
# -----------------------------------------------------------------------------
@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_destination_should_be_device(mtp):
    """
    Test if Sync sets device as destination if computer is the source
    """
    sync = Sync(mtp, COMPUTER_SOURCE, '')
    assert sync.destination == os.path.join(mtp, '')


@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_destination_should_be_computer(mtp):
    """
    Test if Sync sets computer as destination if device is the source
    """
    sync = Sync(mtp, DEVICE_SOURCE, '')
    assert sync.destination == os.path.join(CURRENT_DIRECTORY, '')
