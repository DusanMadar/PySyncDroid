"""Tests for Sync functionality"""


import errno
import getpass
from mock import patch
import os
import random
import shutil
import string
import tempfile
import time

import pytest

import pysyncdroid
from pysyncdroid import gvfs
from pysyncdroid.exceptions import DeviceException
from pysyncdroid.find_device import get_connection_details, get_mtp_details
from pysyncdroid.sync import Sync
from pysyncdroid.sync import REMOVE, SYNCHRONIZE


#: Constants
CURRENT_DIRECTORY = os.getcwd()
CURRENT_USER = getpass.getuser()

# tmpdir name
PYSYNCDROID = 'pysyncdroid_'

# computer
COMPUTER_HOME = '/home/{u}'.format(u=CURRENT_USER)
COMPUTER_SOURCE = os.path.join(COMPUTER_HOME, 'Music')
COMPUTER_SOURCE_FILE = os.path.join(COMPUTER_HOME, '.bashrc')

# device
# NOTE update these constants to match your device name and/or settings
DEVICE_VENDOR = 'samsung'
DEVICE_MODEL = 'galaxy'
DEVICE_SOURCE = 'Card/Music'
DEVICE_SOURCE_FAKE = 'CCard/Music'
DEVICE_DESTINATION = DEVICE_SOURCE
DEVICE_DESTINATION_TEST_DIR = (DEVICE_DESTINATION + os.sep + PYSYNCDROID +
                               ''.join(random.sample(string.ascii_letters, 6)))
DEVICE_MTP_FAKE = ('mtp://[usb:<usb_id>,<device_id>]/', '/mtp_path')

DEVICE_NOT_CONNECTED = "Testing device not connected"

# expected exception messages
NOT_EXISTS = 'does not exist on computer or on device'
NOT_DIRECTORY = 'is not a directory'


def device_not_connected():
    """
    Helper - check if testing device not connected

    :returns bool

    """
    try:
        get_connection_details(vendor=DEVICE_VENDOR, model=DEVICE_MODEL)
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
        _, path = tempfile.mkstemp(prefix=PYSYNCDROID, suffix='.txt', dir=tmpdir)  # noqa
        tmpfiles.append(path)

    return tmpfiles


@pytest.fixture(scope='module')
def tmpfiles_names(tmpfiles):
    """
    Fixture - get a list (actually, a set) of tempfile names.

    :argument tmpdir: tmpfiles fixture
    :type tmpdir: fixture

    :returns set

    """
    tmpfiles_names = set([os.path.basename(tmpf) for tmpf in tmpfiles
                          if os.path.isfile(tmpf)])

    return tmpfiles_names


@pytest.fixture()
def tmpdir_device_remove(request, mtp):
    """
    Fixture - remove device temporary directory

    :argument mtp: mtp fixture
    :type mtp: fixture

    """
    def fin():
        device_destination = os.path.join(mtp[1], DEVICE_DESTINATION_TEST_DIR)
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
    usb_bus, device = get_connection_details(vendor=DEVICE_VENDOR,
                                             model=DEVICE_MODEL)
    mtp_details = get_mtp_details(usb_bus, device)

    return mtp_details


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
    sync.set_source_abs()

    assert sync.source == os.path.join(mtp[1], DEVICE_SOURCE)


@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_source_not_exists_on_device(mtp):
    """
    Test if Sync is not able to initialize; i.e. source doesn't exists
    """
    with pytest.raises(OSError) as exc:
        sync = Sync(mtp, DEVICE_SOURCE_FAKE, '')
        sync.set_source_abs()

    assert NOT_EXISTS in str(exc.value)


# computer source tests -------------------------------------------------------
# -----------------------------------------------------------------------------
def test_source_exists_on_computer():
    """
    Test if Sync is able to initialize; i.e. source exists and is a directory
    """
    sync = Sync(('', ''), COMPUTER_SOURCE, '')
    sync.set_source_abs()

    assert sync.source == COMPUTER_SOURCE


def test_source_exists_on_computer_relative(cd_home, cd_back):
    """
    Test if Sync is able to initialize; i.e. source exists and is a directory
    even if is specified as a relative path which is OK in this context
    """
    music = 'Music'

    sync = Sync(('', ''), music, '')
    sync.set_source_abs()

    assert sync.source == os.path.join(COMPUTER_HOME, music)


def test_source_exists_on_computer_relative2(cd_home, cd_back):
    """
    Test if Sync is able to initialize; i.e. source exists and is a directory
    even if is specified as a relative path
    """
    parent = '..'

    sync = Sync(('', ''), parent, '')
    sync.set_source_abs()

    assert sync.source == os.path.dirname(COMPUTER_HOME)


def test_source_exists_on_computer_relative3(cd_home, cd_back):
    """
    Test if Sync is able to initialize; i.e. source exists and is a directory
    even if is specified as a relative path
    """
    parent = os.sep

    sync = Sync(('', ''), parent, '')
    sync.set_source_abs()

    assert sync.source == os.sep


def test_source_not_exists_on_computer_relative():
    """
    Test if Sync is not able to initialize; i.e. source doesn't exists as it
    is specified as a relative path which is wrong in this context
    """
    with pytest.raises(OSError) as exc:
        sync = Sync(('', ''), 'Music/', '')
        sync.set_source_abs()

    assert NOT_EXISTS in str(exc.value)


def test_source_expand():
    """
    Test if Sync is able to initialize even if given an expandable path
    """
    sync = Sync(('', ''), '~/Music', '')
    sync.set_source_abs()

    assert sync.source == os.path.join(COMPUTER_HOME, 'Music')


def test_source_is_a_file_on_computer():
    """
    Test if Sync is not able to initialize; i.e. source is a not a directory
    """
    with pytest.raises(OSError) as exc:
        sync = Sync(('', ''), COMPUTER_SOURCE_FILE, '')
        sync.set_source_abs()

    assert NOT_DIRECTORY in str(exc.value)


# destination tests -----------------------------------------------------------
# -----------------------------------------------------------------------------
def test_destination_should_be_device():
    """
    Test if Sync sets device as destination if computer is the source
    """
    sync = Sync(DEVICE_MTP_FAKE, COMPUTER_SOURCE, '')
    sync.set_source_abs()
    sync.set_destination_abs()

    assert sync.destination == os.path.join(DEVICE_MTP_FAKE[1], '')


@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_destination_should_be_computer(mtp):
    """
    Test if Sync sets computer as destination if device is the source
    """
    sync = Sync(mtp, DEVICE_SOURCE, 'computer-desc/')
    sync.set_source_abs()
    sync.set_destination_abs()

    assert sync.destination == os.path.join(CURRENT_DIRECTORY, 'computer-desc')


@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_destination_should_be_computer_relative(mtp):
    """
    Test if Sync sets computer as destination if device is the source and the
    destination is a relative path
    """
    parent = '../..'

    sync = Sync(mtp, DEVICE_SOURCE, parent)
    sync.set_source_abs()
    sync.set_destination_abs()

    assert sync.destination == COMPUTER_HOME


# paths preparation tests -----------------------------------------------------
# -----------------------------------------------------------------------------
@patch.object(pysyncdroid.sync.Sync, 'gvfs_wrapper')
def test_get_sync_data(mock_gvfs_wrapper, tmpdir, tmpfiles):
    """
    Test if Sync.get_sync_data() returns an expected list of paths
    """
    mock_gvfs_wrapper.return_value = ''

    sync = Sync(DEVICE_MTP_FAKE, tmpdir, DEVICE_DESTINATION)
    sync.set_source_abs()
    sync.set_destination_abs()

    for to_sync in sync.get_sync_data():
        for key in ('src_dir_abs', 'src_dir_fls', 'dst_dir_abs', 'dst_dir_fls'):
            assert key in to_sync

        for src in to_sync['src_dir_fls']:
            basename = os.path.basename(src)
            dst = src.replace(to_sync['src_dir_abs'], to_sync['dst_dir_abs'])

            assert src.endswith(basename)
            assert dst.endswith(basename)

            assert tmpdir in src
            assert DEVICE_MTP_FAKE[1] in dst
            assert DEVICE_DESTINATION in dst


@pytest.mark.parametrize("file_type", ['txt', 'TXT'])
@patch.object(pysyncdroid.sync.Sync, 'gvfs_wrapper')
def test_get_sync_data_ignore_files(mock_gvfs_wrapper, tmpdir, tmpfiles, file_type):
    """
    Test if Sync.get_sync_data() ignores given file types
    """
    mock_gvfs_wrapper.return_value = ''

    sync = Sync(DEVICE_MTP_FAKE, tmpdir, DEVICE_DESTINATION,
                ignore_file_types=[file_type])
    sync.set_source_abs()
    sync.set_destination_abs()

    for to_sync in sync.get_sync_data():
        assert not to_sync['src_dir_fls']


# synchronization tests -------------------------------------------------------
# -----------------------------------------------------------------------------
@pytest.mark.first
@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_sync_empty_dir(mtp, tmpdir):
    """
    Test Sync.sync() doesn't sync an empty directory
    """
    sync = Sync(mtp, tmpdir, DEVICE_DESTINATION_TEST_DIR)
    sync.set_source_abs()
    sync.set_destination_abs()
    sync.sync()

    with pytest.raises(OSError):
        os.listdir(sync.destination)


@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_sync_to_device(mtp, tmpdir, tmpfiles_names, tmpdir_device_remove):
    """
    Test if Sync.sync() really sync files from computer to device
    """
    sync = Sync(mtp, tmpdir, DEVICE_DESTINATION_TEST_DIR)
    sync.set_source_abs()
    sync.set_destination_abs()
    sync.sync()

    synced_files = os.listdir(sync.destination)
    assert synced_files

    for synced_file in synced_files:
        synced_file = os.path.basename(synced_file)

        assert synced_file in tmpfiles_names


@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_sync_to_computer(mtp, tmpdir, tmpfiles, tmpfiles_names, tmpdir_device_remove):  # noqa
    """
    Test if Sync.sync() really sync files from device to computer
    """
    #
    # first move tmpfiles to the device
    device_source = os.path.join(mtp[1], DEVICE_DESTINATION_TEST_DIR)

    if not os.path.exists(device_source):
        gvfs.mkdir(device_source)

    for tmpfile in tmpfiles:
        gvfs.mv(tmpfile, os.path.join(mtp[1], device_source))

    moved_files = os.listdir(device_source)
    assert moved_files

    for moved_file in moved_files:
        moved_file = os.path.basename(moved_file)

        assert moved_file in tmpfiles_names

    #
    # then sync them back to computer
    sync = Sync(mtp, device_source, tmpdir)
    sync.set_source_abs()
    sync.set_destination_abs()
    sync.sync()

    synced_files = os.listdir(sync.destination)
    assert synced_files

    for synced_file in synced_files:
        synced_file = os.path.basename(synced_file)

        assert synced_file in tmpfiles_names


@pytest.mark.parametrize("unmatched_action", [REMOVE, SYNCHRONIZE])
@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_sync_to_device_unmatched(mtp, tmpdir, tmpfiles_names,
                                  tmpdir_device_remove, unmatched_action):
    """
    :unmatched_action == SYNCHRONIZE

    Test if Sync.sync() really sync files from computer to device and sync
    back to computer file(s) that are only on the device.


    :unmatched_action == REMOVE

    Test if Sync.sync() really sync files from computer to device and remove
    files that are only on the device.
    """
    #
    # create parent directory and copy a new file to the device
    # destination directory; this copied file will be the unmatched file, i.e.
    # a file that is present only in the destination directory
    unmatched = 'test.test'

    dst_pth = os.path.join(mtp[1], DEVICE_DESTINATION_TEST_DIR)
    gvfs.mkdir(dst_pth)

    dst_file = os.path.join(dst_pth, unmatched)
    gvfs.cp(src=COMPUTER_SOURCE_FILE, dst=dst_file)

    sync = Sync(mtp, tmpdir, DEVICE_DESTINATION_TEST_DIR, unmatched=unmatched_action)  # noqa
    sync.set_source_abs()
    sync.set_destination_abs()
    sync.sync()

    #
    # exclude the unmatched file from synchronized files as it was already in
    # the destination directory
    synced_files = [syncf for syncf in os.listdir(sync.destination)
                    if syncf != unmatched]
    assert synced_files

    for synced_file in synced_files:
        synced_file = os.path.basename(synced_file)

        assert synced_file in tmpfiles_names

    #
    # test if unmatched_action works as expected
    if unmatched_action == SYNCHRONIZE:
        # unmatched file should be synchronized to the source directory
        assert unmatched in os.listdir(sync.source)
    elif unmatched_action == REMOVE:
        # unmatched file should be removed from the destination directory
        assert unmatched not in os.listdir(sync.destination)


@pytest.mark.parametrize("overwrite", [True, False])
@pytest.mark.skipif(device_not_connected(), reason=DEVICE_NOT_CONNECTED)
def test_sync_to_device_overwrite(mtp, tmpdir, tmpfiles, tmpdir_device_remove,
                                  overwrite):
    """
    :overwrite == True

    Test if Sync.sync() overwrites existing files


    :overwrite == False

    Test if Sync.sync() does not overwrite existing files
    """
    def _get_modification_times():
        sync_dict = {}

        for synced_file in os.listdir(sync.destination):
            abs_pth = os.path.join(sync.destination, synced_file)
            sync_dict[synced_file] = time.ctime(os.path.getmtime(abs_pth))

            return sync_dict

    sync = Sync(mtp, tmpdir, DEVICE_DESTINATION_TEST_DIR, overwrite_existing=overwrite)  # noqa
    sync.set_source_abs()
    sync.set_destination_abs()

    sync.sync()
    first_sync = _get_modification_times()

    time.sleep(2)

    sync.sync()
    second_sync = _get_modification_times()

    for synced_file in first_sync:
        if overwrite:
            assert first_sync[synced_file] < second_sync[synced_file]
        else:
            assert first_sync[synced_file] == second_sync[synced_file]
