"""Tests for Sync functionality"""


import os
import errno
import pytest
import random
import string
import shutil
import getpass
import tempfile

from pysyncdorid.sync import Sync

from pysyncdorid import utils_gvfs as gvfs
from pysyncdorid.exceptions import DeviceException
from pysyncdorid.find_device import connection_details, get_mtp_path


#: Constants
CURRENT_DIRECTORY = os.getcwd()
CURRENT_USER = getpass.getuser()

# tmpdir
PYSYNCDROID = 'pysyncdroid_'

COMPUTER_HOME = '/home/{u}/'.format(u=CURRENT_USER)
COMPUTER_SOURCE = os.path.join(COMPUTER_HOME, 'Music')
COMPUTER_SOURCE_FILE = os.path.join(COMPUTER_HOME, '.bashrc')

DEVICE_VENDOR = 'samsung'
DEVICE_MODEL = 'gt-i9300'
DEVICE_SOURCE = 'Card/Music'
DEVICE_SOURCE_FAKE = 'CCard/Music'
DEVICE_DESTINATION = DEVICE_SOURCE
DEVICE_DESTINATION_TEST = (DEVICE_DESTINATION + os.sep + PYSYNCDROID +
                           ''.join(random.sample(string.ascii_letters, 6)))
DEVICE_MTP_FAKE = '/mtp_path'

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


@pytest.fixture(scope='session', autouse=True)
def tmpdir(request):
    """
    Fixture - create/remove temporary directory

    :returns str

    """
    tmpdir = tempfile.mkdtemp(prefix=PYSYNCDROID, suffix='_testing')

    def fin():
        try:
            shutil.rmtree(tmpdir)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    request.addfinalizer(fin)
    return tmpdir


@pytest.fixture(scope='module')
def tmpfiles(tmpdir):
    """
    Fixture - create 20 test *.txt files

    :argument tmpdir: tmpdir fixture
    :type tmpdir: fixture

    :returns list

    """
    tmpfiles = []
    for _ in range(21):
        _, path = tempfile.mkstemp(prefix=PYSYNCDROID, suffix='.txt', dir=tmpdir)  # NOQA
        tmpfiles.append(path)

    return tmpfiles


@pytest.fixture()
def tmpdir_device_remove(request, mtp):
    """
    Fixture - remove device temporary directory

    :argument mtp: mtp fixture
    :type mtp: fixture

    """
    def fin():
        device_destination = os.path.join(mtp, DEVICE_DESTINATION_TEST)
        gvfs.rm(device_destination)

        if os.path.exists(device_destination):
            raise OSError('Failed to remove device directory "{d}"'.
                          format(d=device_destination))

    request.addfinalizer(fin)


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
def test_destination_should_be_device():
    """
    Test if Sync sets device as destination if computer is the source
    """
    sync = Sync(DEVICE_MTP_FAKE, COMPUTER_SOURCE, '')
    assert sync.destination == os.path.join(DEVICE_MTP_FAKE, '')


@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_destination_should_be_computer(mtp):
    """
    Test if Sync sets computer as destination if device is the source
    """
    sync = Sync(mtp, DEVICE_SOURCE, '')
    assert sync.destination == os.path.join(CURRENT_DIRECTORY, '')


# paths preparation tests -----------------------------------------------------
# -----------------------------------------------------------------------------
def test_prepare_paths(tmpdir, tmpfiles):
    """
    Test if Sync.prepare_paths() returns an expected list of paths
    """
    sync = Sync(DEVICE_MTP_FAKE, tmpdir, DEVICE_DESTINATION)

    for to_sync in sync.prepare_paths():
        for key in ('abs_src_dir', 'abs_dst_dir', 'abs_fls_map'):
            assert key in to_sync

        for src, dst in to_sync['abs_fls_map']:
            basename = os.path.basename(src)

            assert src.endswith(basename)
            assert dst.endswith(basename)

            assert tmpdir in src
            assert DEVICE_MTP_FAKE in dst
            assert DEVICE_DESTINATION in dst


# synchronization tests -------------------------------------------------------
# -----------------------------------------------------------------------------
@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_sync_to_device(mtp, tmpdir, tmpfiles, tmpdir_device_remove):
    """
    Test if Sync.sync() really sync files from computer to device
    """
    sync = Sync(mtp, tmpdir, DEVICE_DESTINATION_TEST)
    sync.sync()

    tmpfiles_names = set([os.path.basename(tmpf) for tmpf in tmpfiles])

    synced_files = os.listdir(sync.destination)
    assert synced_files

    for synced_file in synced_files:
        synced_file = os.path.basename(synced_file)

        assert synced_file in tmpfiles_names


@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_sync_to_computer(mtp, tmpdir, tmpfiles, tmpdir_device_remove):
    """
    Test if Sync.sync() really sync files from device to computer
    """
    tmpfiles_names = set([os.path.basename(tmpf) for tmpf in tmpfiles])

    #
    # first move tmpfiles to the device
    device_source = os.path.join(mtp, DEVICE_DESTINATION_TEST)

    if not os.path.exists(device_source):
        gvfs.mkdir(device_source)

    for tmpfile in tmpfiles:
        gvfs.mv(tmpfile, os.path.join(mtp, device_source))

    moved_files = os.listdir(device_source)
    assert moved_files

    for moved_file in moved_files:
        moved_file = os.path.basename(moved_file)

        assert moved_file in tmpfiles_names

    #
    # then sync them back to computer
    sync = Sync(mtp, device_source, tmpdir)
    sync.sync()

    synced_files = os.listdir(sync.destination)
    assert synced_files

    for synced_file in synced_files:
        synced_file = os.path.basename(synced_file)

        assert synced_file in tmpfiles_names
