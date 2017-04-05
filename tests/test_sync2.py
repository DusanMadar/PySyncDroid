"""Tests for synchronization functionality."""


from mock import patch
import os
from StringIO import StringIO
import unittest

import pysyncdroid
from pysyncdroid.exceptions import BashException, IgnoredTypeException
from pysyncdroid.gvfs import mkdir
from pysyncdroid.find_device import MTP_URL_PATTERN, MTP_GVFS_PATH_PATTERN
from pysyncdroid.sync import Sync, readlink


FAKE_MTP_DETAILS = (
    MTP_URL_PATTERN.format(b='002', d='003'),
    MTP_GVFS_PATH_PATTERN.format(u='<user>', b='002', d='003')
)


class TestReadLink(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('pysyncdroid.utils.run_bash_cmd')
        self.mock_run_bash_cmd = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_readlink_no_path(self):
        """
        Test 'readlink' returns an empty string in case of no path to read.
        """
        self.assertEqual(readlink(''), '')

    @patch('pysyncdroid.sync.os.path.expanduser')
    def test_readlink_tilde(self, mock_expanduser):
        """
        Test 'readlink' is able to hadle '~' path.
        """
        mock_expanduser.return_value = '/home/<user name>'
        self.mock_run_bash_cmd.return_value = mock_expanduser.return_value
        self.assertEqual(readlink('~'), mock_expanduser.return_value)

    def test_readlink_slash(self):
        """
        Test 'readlink' is able to hadle '/' path (and doesn't strip it).
        """
        self.mock_run_bash_cmd.return_value = '/'
        self.assertEqual(readlink('/'), '/')

    def test_readlink_nonexisting(self):
        """
        Test 'readlink' is agnosting to the path existance and simply adds the
        provided string (without a slash) to the current working directory.
        """
        self.mock_run_bash_cmd.return_value = os.path.join(os.getcwd(), 'foo')
        self.assertEqual(readlink('foo'), self.mock_run_bash_cmd.return_value)

    def test_readlink_device_path(self):
        """
        Test 'readlink' returns the given path if it's unable to follow it.
        """
        self.mock_run_bash_cmd.return_value = 'Phone/Card'
        self.assertEqual(readlink('Phone/Card'), 'Phone/Card')


class TestSync(unittest.TestCase):
    def _create_sync_data(self, sync):
        """
        Create sync data dictionary.

        :argument sync_data: sync data dictionary
        :type sync_data: dict

        :returns dict

        """
        src_subdir_abs = os.path.join(sync.source, 'testdir')
        dst_subdir_abs = os.path.join(sync.destination, 'testdir')

        return sync.sync_data_template(src_subdir_abs, dst_subdir_abs)

    #
    # '_verbose()'
    @patch('sys.stdout', new_callable=StringIO)
    def test_verbose_active(self, mock_stdout):
        """
        Test '_verbose' prints a given message in verbose mode.
        """
        sync = Sync(FAKE_MTP_DETAILS, '', '', verbose=True)

        test_message = 'Hello World!'
        sync._verbose(test_message)
        self.assertEqual(test_message, mock_stdout.getvalue().strip())

    @patch('sys.stdout', new_callable=StringIO)
    def test_verbose_inactive(self, mock_stdout):
        """
        Test '_verbose' doesn't print a given message if not in verbose mode.
        """
        sync = Sync(FAKE_MTP_DETAILS, '', '', verbose=False)

        sync._verbose('Hello World!')
        self.assertEqual('', mock_stdout.getvalue().strip())

    #
    # 'gvfs_wrapper()'
    @patch('pysyncdroid.gvfs.mkdir')
    def test_gvfs_wrapper_common_exception(self, mock_mkdir):
        """
        Test 'gvfs_wrapper' isn't ignoring common exceptions.
        """
        mock_mkdir.side_effect = ValueError
        sync = Sync(FAKE_MTP_DETAILS, '', '')

        with self.assertRaises(ValueError):
            sync.gvfs_wrapper(mock_mkdir, '/tmp/dir')

    @patch('pysyncdroid.gvfs.mkdir')
    def test_gvfs_wrapper_bash_exception_any(self, mock_mkdir):
        """
        Test 'gvfs_wrapper' doesn't handle any BashException.
        """
        mock_mkdir.side_effect = BashException
        sync = Sync(FAKE_MTP_DETAILS, '', '')

        with self.assertRaises(BashException):
            sync.gvfs_wrapper(mock_mkdir, '/tmp/dir')

    @patch('pysyncdroid.gvfs.mkdir')
    @patch('pysyncdroid.gvfs.mount')
    def test_gvfs_wrapper_bash_exception_exact(self, mock_mount, mock_mkdir):
        """
        Test 'gvfs_wrapper' handles only a specific BashException.
        """
        mock_mkdir.side_effect = [
            BashException('Connection reset by peer'),
            None,
        ]
        sync = Sync(FAKE_MTP_DETAILS, '', '')
        sync.gvfs_wrapper(mock_mkdir, '/tmp/dir')

        self.assertEqual(mock_mkdir.call_count, 2)
        mock_mount.assert_called_once_with(sync.mtp_url)

    #
    # 'set_source_abs()'
    @patch('pysyncdroid.sync.os.path.isdir')
    @patch('pysyncdroid.sync.os.path.exists')
    def test_set_source_abs_absolute_path(
        self, mock_path_exists, mock_path_isdir
    ):
        """
        Test 'set_source_abs' recongizes an absolute path.
        """
        mock_path_exists.return_value = True
        mock_path_isdir.return_value = True

        sync = Sync(FAKE_MTP_DETAILS, '/an-absolute-path', '')
        sync.set_source_abs()

        self.assertEqual(sync.source, '/an-absolute-path')

    @patch('pysyncdroid.sync.os.path.isdir')
    @patch('pysyncdroid.sync.os.path.exists')
    def test_set_source_abs_computer_relative_path(
        self, mock_path_exists, mock_path_isdir
    ):
        """
        Test 'set_source_abs' creates an absolute path from a relative path
        when the path exists on computer.
        """
        mock_path_exists.return_value = True
        mock_path_isdir.return_value = True

        sync = Sync(FAKE_MTP_DETAILS, 'a-relative-path/', '')
        sync.set_source_abs()

        expected_abs_path = os.path.join(os.getcwd(), 'a-relative-path')
        self.assertEqual(sync.source, expected_abs_path)

    @patch('pysyncdroid.sync.os.path.isdir')
    @patch('pysyncdroid.sync.os.path.exists')
    def test_set_source_abs_device_relative_path(
        self, mock_path_exists, mock_path_isdir
    ):
        """
        Test 'set_source_abs' creates an absolute path from a relative path
        when the path exists on device.
        """
        mock_path_exists.side_effect = [False, True, True]
        mock_path_isdir.return_value = True

        sync = Sync(FAKE_MTP_DETAILS, 'Card/Music', '')
        sync.set_source_abs()

        expected_abs_path = os.path.join(sync.mtp_gvfs_path, 'Card/Music')
        self.assertEqual(sync.source, expected_abs_path)

    @patch('pysyncdroid.sync.os.path.exists')
    def test_set_source_abs_nonexistent(self, mock_path_exists):
        """
        Test 'set_source_abs' raises an OSError when source doesn't exist on
        the computer or on the device.
        """
        mock_path_exists.return_value = False

        with self.assertRaises(OSError) as exc:
            sync = Sync(FAKE_MTP_DETAILS, 'non-exiting-path', '')
            sync.set_source_abs()

        # Must be called twice - for computer and device.
        self.assertEqual(mock_path_exists.call_count, 2)

        self.assertEqual(
            str(exc.exception),
            '"non-exiting-path" does not exist on computer or on device.'
        )

    @patch('pysyncdroid.sync.os.path.isdir')
    @patch('pysyncdroid.sync.os.path.exists')
    def test_set_source_abs_not_directory(
        self, mock_path_exists, mock_path_isdir
    ):
        """
        Test 'set_source_abs' raises an OSError when source exists but is not a
        directory.
        """
        mock_path_exists.return_value = True
        mock_path_isdir.return_value = False

        with self.assertRaises(OSError) as exc:
            sync = Sync(FAKE_MTP_DETAILS, 'not-a-directory', '')
            sync.set_source_abs()

        expected_abs_path = os.path.join(os.getcwd(), 'not-a-directory')
        err_msg = '"{}" is not a directory.'.format(expected_abs_path)
        self.assertEqual(str(exc.exception), err_msg)

    #
    # 'set_destination_abs()'
    def test_set_destination_abs_absolute_path(self):
        """
        Test 'set_destination_abs' recongizes an absolute path.
        """
        sync = Sync(FAKE_MTP_DETAILS, '', '/an-absolute-path')
        sync.set_destination_abs()

        self.assertEqual(sync.destination, '/an-absolute-path')

    def test_set_destination_abs_computer_relative_path(self):
        """
        Test 'set_destination_abs' creates an absolute path from a relative path
        when the destination is on computer.
        """
        sync = Sync(FAKE_MTP_DETAILS, '/test-mtp:host-path', 'a-relative-path/')
        sync.set_destination_abs()

        expected_abs_path = os.path.join(os.getcwd(), 'a-relative-path')
        self.assertEqual(sync.destination, expected_abs_path)

    def test_set_destination_abs_device_relative_path(self):
        """
        Test 'set_destination_abs' creates an absolute path from a relative path
        when the destination is on device.
        """

        sync = Sync(FAKE_MTP_DETAILS, '', 'Card/Music')
        sync.set_destination_abs()

        expected_abs_path = os.path.join(sync.mtp_gvfs_path, 'Card/Music')
        self.assertEqual(sync.destination, expected_abs_path)

    #
    # 'set_destination_subdir_abs()'
    def test_set_destination_subdir_absh(self):
        """
        Test 'set_destination_subdir_abs' creates an absolute path for a
        destination subdirectory.
        """
        sync = Sync(FAKE_MTP_DETAILS, '~/Music', 'Card/Music')
        sync.set_source_abs()
        sync.set_destination_abs()

        src_subdir_abs = os.path.join(sync.source, 'testdir')
        dst_subdir_abs = sync.set_destination_subdir_abs(src_subdir_abs)

        expected_abs_path = os.path.join(sync.destination, 'testdir')
        self.assertEqual(dst_subdir_abs, expected_abs_path)

    #
    # 'sync_data_template()'
    def test_sync_data_template(self):
        """
        Test 'sync_data_template' creates a dict with expected keys.
        """
        sync = Sync(FAKE_MTP_DETAILS, '~/Music', 'Card/Music')
        sync.set_source_abs()
        sync.set_destination_abs()

        src_subdir_abs = os.path.join(sync.source, 'testdir')
        dst_subdir_abs = os.path.join(sync.destination, 'testdir')
        sync_data = sync.sync_data_template(src_subdir_abs, dst_subdir_abs)

        self.assertIsInstance(sync_data, dict)
        self.assertIn('src_dir_abs', sync_data)
        self.assertIn('src_dir_fls', sync_data)
        self.assertIn('dst_dir_abs', sync_data)
        self.assertIn('dst_dir_fls', sync_data)

    #
    # 'handle_ignored_file_type()'
    def test_handle_ignored_file_type(self):
        """
        Test 'handle_ignored_file_type' raises IgnoredTypeException exception
        only for files with specified extensions.
        """
        sync = Sync(FAKE_MTP_DETAILS, '', '', ignore_file_types=['jpg'])

        sync.handle_ignored_file_type('/tmp/test.png')

        with self.assertRaises(IgnoredTypeException):
            sync.handle_ignored_file_type('/tmp/test.jpg')

    #
    # 'get_source_subdir_data()'
    @patch.object(pysyncdroid.sync.Sync, 'handle_ignored_file_type')
    def test_get_source_subdir_data(self, mock_handle_ignored_file_type):
        """
        Test 'get_source_subdir_data' populates 'src_dir_fls' with collected
        data.
        """
        mock_handle_ignored_file_type.side_effect = [
            None, IgnoredTypeException, None
        ]

        sync = Sync(FAKE_MTP_DETAILS, '/tmp', 'Card/Music')
        sync_data = self._create_sync_data(sync)

        src_subdir_files = ['song.mp3', 'cover.jpg', 'demo.mp3']
        sync.get_source_subdir_data(src_subdir_files, sync_data)

        self.assertEqual(sync_data['src_dir_fls'], [
            '/tmp/testdir/song.mp3', '/tmp/testdir/demo.mp3'
        ])

    #
    # 'get_destination_subdir_data()'
    @patch('pysyncdroid.sync.os.path.exists')
    @patch.object(pysyncdroid.sync.Sync, 'gvfs_wrapper')
    def test_get_destination_subdir_data_doesnt_exist(
        self, mock_gvfs_wrapper, mock_path_exists
    ):
        """
        Test 'get_destination_subdir_data' creates destination direcotry if it
        doesn't exist.
        """
        mock_path_exists.return_value = False

        sync = Sync(FAKE_MTP_DETAILS, '/tmp', 'Card/Music')
        sync_data = self._create_sync_data(sync)

        sync.get_destination_subdir_data(sync_data)

        mock_gvfs_wrapper.assert_called_once_with(mkdir, 'Card/Music/testdir')
        self.assertFalse(sync_data['dst_dir_fls'])

    @patch('pysyncdroid.sync.os.path.exists')
    @patch('pysyncdroid.sync.os.listdir')
    @patch.object(pysyncdroid.sync.Sync, 'handle_ignored_file_type')
    def test_get_destination_subdir_data_(
        self, mock_handle_ignored_file_type, mock_listdir, mock_path_exists
    ):
        """
        Test 'get_destination_subdir_data' populates 'dst_dir_fls' with
        collected data.
        """
        mock_path_exists.return_value = True
        mock_listdir.return_value = ['song.mp3', 'cover.jpg', 'demo.mp3']
        mock_handle_ignored_file_type.side_effect = [
            None, IgnoredTypeException, None
        ]

        sync = Sync(FAKE_MTP_DETAILS, '/tmp', 'Card/Music')
        sync_data = self._create_sync_data(sync)

        sync.get_destination_subdir_data(sync_data)

        self.assertEqual(sync_data['dst_dir_fls'], [
            'Card/Music/testdir/song.mp3', 'Card/Music/testdir/demo.mp3'
        ])


if __name__ == '__main__':
    unittest.main()
