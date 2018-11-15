"""Tests for synchronization functionality."""


from io import StringIO
import os
import unittest
from unittest.mock import call, patch

import pysyncdroid
from pysyncdroid.exceptions import BashException, IgnoredTypeException
from pysyncdroid.gvfs import cp, mkdir, rm
from pysyncdroid.sync import Sync, readlink, REMOVE, SYNCHRONIZE


FAKE_MTP_DETAILS = (
    "mtp://[usb:002,003]/",
    "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D",
)

FAKE_SYNC_DATA = {
    "src_dir_abs": "/tmp/testdir",
    "src_dir_fls": ["/tmp/testdir/song.mp3", "/tmp/testdir/demo.mp3"],
    "dst_dir_fls": [
        "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/demo.mp3",  # noqa
        "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/oldsong.mp3",  # noqa
    ],
    "dst_dir_abs": "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir",  # noqa
}


class TestReadLink(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("pysyncdroid.utils.run_bash_cmd")
        self.mock_run_bash_cmd = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_readlink_no_path(self):
        """
        Test 'readlink' returns an empty string in case of no path to read.
        """
        self.assertEqual(readlink(""), "")

    @patch("pysyncdroid.sync.os.path.expanduser")
    def test_readlink_tilde(self, mock_expanduser):
        """
        Test 'readlink' hadles '~' path.
        """
        mock_expanduser.return_value = "/home/<user name>"
        self.mock_run_bash_cmd.return_value = mock_expanduser.return_value
        self.assertEqual(readlink("~"), mock_expanduser.return_value)

    def test_readlink_slash(self):
        """
        Test 'readlink' hadles '/' path (and doesn't strip it).
        """
        self.mock_run_bash_cmd.return_value = "/"
        self.assertEqual(readlink("/"), "/")

    def test_readlink_nonexisting(self):
        """
        Test 'readlink' is agnostinc to the path existance and simply adds the
        provided string (without a slash) to the current working directory.
        """
        self.mock_run_bash_cmd.return_value = os.path.join(os.getcwd(), "foo")
        self.assertEqual(readlink("foo"), self.mock_run_bash_cmd.return_value)

    def test_readlink_device_path(self):
        """
        Test 'readlink' returns the given path if it's unable to follow it.
        """
        self.mock_run_bash_cmd.return_value = "Phone/Card"
        self.assertEqual(readlink("Phone/Card"), "Phone/Card")


class TestSync(unittest.TestCase):
    def _create_empty_sync_data(self, sync):
        """
        Create empty sync data dictionary.

        :argument sync: Sync instance
        :type sync: object

        :returns dict

        """
        src_subdir_abs = os.path.join(sync.source, "testdir")
        dst_subdir_abs = os.path.join(sync.destination, "testdir")

        return sync.sync_data_template(src_subdir_abs, dst_subdir_abs)

    #
    # '_verbose()'
    @patch("sys.stdout", new_callable=StringIO)
    def test_verbose_active(self, mock_stdout):
        """
        Test '_verbose' prints a given message if Sync is in verbose mode.
        """
        sync = Sync(FAKE_MTP_DETAILS, "", "", verbose=True)

        test_message = "Hello World!"
        sync._verbose(test_message)
        self.assertEqual(test_message, mock_stdout.getvalue().strip())

    @patch("sys.stdout", new_callable=StringIO)
    def test_verbose_inactive(self, mock_stdout):
        """
        Test '_verbose' doesn't print a given message if Sync isn't in
        verbose mode.
        """
        sync = Sync(FAKE_MTP_DETAILS, "", "", verbose=False)

        sync._verbose("Hello World!")
        self.assertEqual("", mock_stdout.getvalue().strip())

    #
    # 'gvfs_wrapper()'
    @patch("pysyncdroid.gvfs.mkdir")
    def test_gvfs_wrapper_common_exception(self, mock_mkdir):
        """
        Test 'gvfs_wrapper' isn't ignoring common exceptions.
        """
        mock_mkdir.side_effect = ValueError
        sync = Sync(FAKE_MTP_DETAILS, "", "")

        with self.assertRaises(ValueError):
            sync.gvfs_wrapper(mock_mkdir, "/tmp/dir")

    @patch("pysyncdroid.gvfs.mkdir")
    def test_gvfs_wrapper_bash_exception_any(self, mock_mkdir):
        """
        Test 'gvfs_wrapper' doesn't handle any BashException.
        """
        mock_mkdir.side_effect = BashException
        sync = Sync(FAKE_MTP_DETAILS, "", "")

        with self.assertRaises(BashException):
            sync.gvfs_wrapper(mock_mkdir, "/tmp/dir")

    @patch("pysyncdroid.gvfs.mkdir")
    @patch("pysyncdroid.gvfs.mount")
    def test_gvfs_wrapper_bash_exception_exact(self, mock_mount, mock_mkdir):
        """
        Test 'gvfs_wrapper' handles only a specific BashException.
        """
        mock_mkdir.side_effect = [
            BashException("Connection reset by peer"),
            None,
        ]
        sync = Sync(FAKE_MTP_DETAILS, "", "")
        sync.gvfs_wrapper(mock_mkdir, "/tmp/dir")

        self.assertEqual(mock_mkdir.call_count, 2)
        mock_mount.assert_called_once_with(sync.mtp_url)

    #
    # 'set_source_abs()'
    @patch("pysyncdroid.sync.os.path.isdir")
    @patch("pysyncdroid.sync.os.path.exists")
    def test_set_source_abs_absolute_path(
        self, mock_path_exists, mock_path_isdir
    ):
        """
        Test 'set_source_abs' recongizes an absolute path.
        """
        mock_path_exists.return_value = True
        mock_path_isdir.return_value = True

        sync = Sync(FAKE_MTP_DETAILS, "/an-absolute-path", "")
        sync.set_source_abs()

        self.assertEqual(sync.source, "/an-absolute-path")

    @patch("pysyncdroid.sync.os.path.isdir")
    @patch("pysyncdroid.sync.os.path.exists")
    def test_set_source_abs_computer_relative_path(
        self, mock_path_exists, mock_path_isdir
    ):
        """
        Test 'set_source_abs' creates an absolute path from a relative path
        when the path exists on computer.
        """
        mock_path_exists.return_value = True
        mock_path_isdir.return_value = True

        sync = Sync(FAKE_MTP_DETAILS, "a-relative-path/", "")
        sync.set_source_abs()

        expected_abs_path = os.path.join(os.getcwd(), "a-relative-path")
        self.assertEqual(sync.source, expected_abs_path)

    @patch("pysyncdroid.sync.os.path.isdir")
    @patch("pysyncdroid.sync.os.path.exists")
    def test_set_source_abs_device_relative_path(
        self, mock_path_exists, mock_path_isdir
    ):
        """
        Test 'set_source_abs' creates an absolute path from a relative path
        when the path exists on device.
        """
        mock_path_exists.side_effect = [False, True, True]
        mock_path_isdir.return_value = True

        sync = Sync(FAKE_MTP_DETAILS, "Card/Music", "")
        sync.set_source_abs()

        expected_abs_path = os.path.join(sync.mtp_gvfs_path, "Card/Music")
        self.assertEqual(sync.source, expected_abs_path)

    @patch("pysyncdroid.sync.os.path.exists")
    def test_set_source_abs_nonexistent(self, mock_path_exists):
        """
        Test 'set_source_abs' raises an OSError when source doesn't exist on
        the computer or on the device.
        """
        mock_path_exists.return_value = False

        with self.assertRaises(OSError) as exc:
            sync = Sync(FAKE_MTP_DETAILS, "non-exiting-path", "")
            sync.set_source_abs()

        # Must be called twice - for computer and device.
        self.assertEqual(mock_path_exists.call_count, 2)

        self.assertEqual(
            str(exc.exception),
            '"non-exiting-path" does not exist on computer or on device.',
        )

    @patch("pysyncdroid.sync.os.path.isdir")
    @patch("pysyncdroid.sync.os.path.exists")
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
            sync = Sync(FAKE_MTP_DETAILS, "not-a-directory", "")
            sync.set_source_abs()

        expected_abs_path = os.path.join(os.getcwd(), "not-a-directory")
        err_msg = '"{}" is not a directory.'.format(expected_abs_path)
        self.assertEqual(str(exc.exception), err_msg)

    #
    # 'set_destination_abs()'
    def test_set_destination_abs_absolute_path(self):
        """
        Test 'set_destination_abs' recongizes an absolute path.
        """
        sync = Sync(FAKE_MTP_DETAILS, "", "/an-absolute-path")
        sync.set_destination_abs()

        self.assertEqual(sync.destination, "/an-absolute-path")

    def test_set_destination_abs_computer_relative_path(self):
        """
        Test 'set_destination_abs' creates an absolute path from a relative path
        when the destination is on computer.
        """
        sync = Sync(
            FAKE_MTP_DETAILS, "/test-mtp:host-path", "a-relative-path/"
        )
        sync.set_destination_abs()

        expected_abs_path = os.path.join(os.getcwd(), "a-relative-path")
        self.assertEqual(sync.destination, expected_abs_path)

    def test_set_destination_abs_device_relative_path(self):
        """
        Test 'set_destination_abs' creates an absolute path from a relative path
        when the destination is on device.
        """

        sync = Sync(FAKE_MTP_DETAILS, "", "Card/Music")
        sync.set_destination_abs()

        expected_abs_path = os.path.join(sync.mtp_gvfs_path, "Card/Music")
        self.assertEqual(sync.destination, expected_abs_path)

    #
    # 'set_destination_subdir_abs()'
    def test_set_destination_subdir_absh(self):
        """
        Test 'set_destination_subdir_abs' creates an absolute path for a
        destination subdir.
        """
        sync = Sync(FAKE_MTP_DETAILS, "~/Music", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()

        src_subdir_abs = os.path.join(sync.source, "testdir")
        dst_subdir_abs = sync.set_destination_subdir_abs(src_subdir_abs)

        expected_abs_path = os.path.join(sync.destination, "testdir")
        self.assertEqual(dst_subdir_abs, expected_abs_path)

    #
    # 'sync_data_template()'
    def test_sync_data_template(self):
        """
        Test 'sync_data_template' creates a sync data dict with expected keys.
        """
        sync = Sync(FAKE_MTP_DETAILS, "~/Music", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()

        src_subdir_abs = os.path.join(sync.source, "testdir")
        dst_subdir_abs = os.path.join(sync.destination, "testdir")
        sync_data = sync.sync_data_template(src_subdir_abs, dst_subdir_abs)

        self.assertIn("src_dir_abs", sync_data)
        self.assertIn("src_dir_fls", sync_data)
        self.assertIn("dst_dir_abs", sync_data)
        self.assertIn("dst_dir_fls", sync_data)

    #
    # 'handle_ignored_file_type()'
    def test_handle_ignored_file_type(self):
        """
        Test 'handle_ignored_file_type' raises IgnoredTypeException exception
        only for files with specified extensions.
        """
        sync = Sync(FAKE_MTP_DETAILS, "", "", ignore_file_types=["jpg"])
        sync.set_source_abs()
        sync.set_destination_abs()

        # this one is fine
        sync.handle_ignored_file_type("/tmp/test.png")

        # this one should be ignored
        with self.assertRaises(IgnoredTypeException):
            sync.handle_ignored_file_type("/tmp/test.jpg")

    #
    # 'get_source_subdir_data()'
    @patch.object(pysyncdroid.sync.Sync, "handle_ignored_file_type")
    def test_get_source_subdir_data(self, mock_handle_ignored_file_type):
        """
        Test 'get_source_subdir_data' populates 'src_dir_fls' with collected
        data.
        """
        mock_handle_ignored_file_type.side_effect = [
            None,
            IgnoredTypeException,
            None,
        ]
        src_subdir_files = ["song.mp3", "cover.jpg", "demo.mp3"]

        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()
        sync_data = self._create_empty_sync_data(sync)
        sync.get_source_subdir_data(src_subdir_files, sync_data)

        self.assertEqual(
            sync_data["src_dir_fls"],
            ["/tmp/testdir/song.mp3", "/tmp/testdir/demo.mp3"],
        )

    #
    # 'get_destination_subdir_data()'
    @patch("pysyncdroid.sync.os.path.exists")
    @patch.object(pysyncdroid.sync.Sync, "gvfs_wrapper")
    def test_get_destination_subdir_data_doesnt_exist(
        self, mock_gvfs_wrapper, mock_path_exists
    ):
        """
        Test 'get_destination_subdir_data' creates destination direcotry if it
        doesn't exist.
        """
        mock_path_exists.side_effect = (True, False)

        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()
        sync_data = self._create_empty_sync_data(sync)
        sync.get_destination_subdir_data(sync_data)

        mock_gvfs_wrapper.assert_called_once_with(
            mkdir,
            "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir",  # noqa
        )
        self.assertFalse(sync_data["dst_dir_fls"])

    @patch("pysyncdroid.sync.os.path.exists")
    @patch("pysyncdroid.sync.os.listdir")
    @patch.object(pysyncdroid.sync.Sync, "handle_ignored_file_type")
    def test_get_destination_subdir_data_(
        self, mock_handle_ignored_file_type, mock_listdir, mock_path_exists
    ):
        """
        Test 'get_destination_subdir_data' populates 'dst_dir_fls' with
        collected data.
        """
        mock_path_exists.return_value = True
        mock_listdir.return_value = ["song.mp3", "cover.jpg", "demo.mp3"]
        mock_handle_ignored_file_type.side_effect = [
            None,
            IgnoredTypeException,
            None,
        ]

        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()
        sync_data = self._create_empty_sync_data(sync)
        sync.get_destination_subdir_data(sync_data)

        self.assertEqual(
            sync_data["dst_dir_fls"],
            [
                "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/song.mp3",  # noqa
                "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/demo.mp3",  # noqa
            ],
        )

    #
    # 'get_sync_data()'
    @patch("pysyncdroid.sync.os.walk")
    @patch.object(pysyncdroid.sync.Sync, "set_destination_subdir_abs")
    @patch.object(pysyncdroid.sync.Sync, "get_destination_subdir_data")
    def test_get_sync_data(
        self,
        mock_get_destination_subdir_data,
        mock_set_destination_subdir_abs,
        mock_oswalk,
    ):
        """
        Test 'get_sync_data' gets list of valid sync_data dictionaries.
        """
        mock_oswalk.return_value = (
            ("/tmp/testdir", ["testsubdir"], ["song.mp3", "demo.mp3"]),
            ("/tmp/testdir/testsubdir", ["testsubdir2"], []),
            ("/tmp/testdir/testsubdir/testsubdir2", [], ["song2.mp3"]),
        )
        mock_set_destination_subdir_abs.side_effect = (
            "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir",  # noqa
            "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/testsubdir2",  # noqa
        )

        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()
        sync_data_set = sync.get_sync_data()

        self.assertTrue(mock_set_destination_subdir_abs.call_count, 2)
        self.assertTrue(mock_get_destination_subdir_data.call_count, 2)

        expected_sync_data_set = [
            {
                "src_dir_abs": "/tmp/testdir",
                "src_dir_fls": [
                    "/tmp/testdir/song.mp3",
                    "/tmp/testdir/demo.mp3",
                ],
                "dst_dir_fls": [],
                "dst_dir_abs": "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir",  # noqa
            },
            {
                "src_dir_abs": "/tmp/testdir/testsubdir/testsubdir2",
                "src_dir_fls": [
                    "/tmp/testdir/testsubdir/testsubdir2/song2.mp3"
                ],
                "dst_dir_fls": [],
                "dst_dir_abs": "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/testsubdir2",  # noqa
            },
        ]

        self.assertIsInstance(sync_data_set, list)
        self.assertEqual(sync_data_set, expected_sync_data_set)

    #
    # 'copy_file()'
    @patch.object(pysyncdroid.sync.Sync, "gvfs_wrapper")
    def test_copy_file(self, mock_gfvs_wrapper):
        """
        Test 'copy_file' copies a file from source to destination.
        """
        src_file = "/tmp/song.mp3"
        dst_file = "Card/Musicsong.mp3"

        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()
        sync.copy_file(src_file, dst_file)

        mock_gfvs_wrapper.assert_called_once_with(cp, src_file, dst_file)

    #
    # 'do_sync()'
    @patch.object(pysyncdroid.sync.Sync, "copy_file")
    def test_do_sync(self, mock_copy_file):
        """
        Test 'do_sync' copies source files to their destination and updates
        destination files list.
        """
        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()
        sync.do_sync(FAKE_SYNC_DATA)

        self.assertEqual(
            FAKE_SYNC_DATA["dst_dir_fls"],
            [
                "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/oldsong.mp3"
            ],  # noqa
        )

        mock_copy_file.assert_called_once_with(
            "/tmp/testdir/song.mp3",
            "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/song.mp3",  # noqa
        )

    @patch.object(pysyncdroid.sync.Sync, "copy_file")
    def test_do_sync_overwrite(self, mock_copy_file):
        """
        Test 'do_sync' is able to overwrite existing destination files.
        """
        sync = Sync(
            FAKE_MTP_DETAILS, "/tmp", "Card/Music", overwrite_existing=True
        )
        sync.set_source_abs()
        sync.set_destination_abs()
        sync.do_sync(FAKE_SYNC_DATA)

        calls = (
            call(
                "/tmp/testdir/song.mp3",
                "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/song.mp3",  # noqa
            ),
            call(
                "/tmp/testdir/demo.mp3",
                "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/demo.mp3",  # noqa
            ),
        )
        mock_copy_file.assert_has_calls(calls)

    #
    # 'handle_destination_dir_data()'
    @patch.object(pysyncdroid.sync.Sync, "gvfs_wrapper")
    def test_handle_destination_dir_data_no_files(self, mock_gfvs_wrapper):
        """
        Test 'handle_destination_dir_data' ends early when there are no data
        to process.
        """
        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music", unmatched=REMOVE)
        sync.set_source_abs()
        sync.set_destination_abs()
        sync.handle_destination_dir_data({"dst_dir_fls": []})

        mock_gfvs_wrapper.assert_not_called()

    @patch.object(pysyncdroid.sync.Sync, "gvfs_wrapper")
    def test_handle_destination_dir_data_remove(self, mock_gfvs_wrapper):
        """
        Test 'handle_destination_dir_data' removes unmatched destination data.
        """
        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music", unmatched=REMOVE)
        sync.set_source_abs()
        sync.set_destination_abs()
        sync.handle_destination_dir_data(
            {
                "dst_dir_fls": [
                    "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/song.mp3"  # noqa
                ]
            }
        )

        mock_gfvs_wrapper.assert_called_once_with(
            rm,
            "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/song.mp3",  # noqa
        )

    @patch.object(pysyncdroid.sync.Sync, "copy_file")
    def test_handle_destination_dir_data_sync(self, mock_copy_file):
        """
        Test 'handle_destination_dir_data' synchronizes unmatched destination
        data to source.
        """
        sync = Sync(
            FAKE_MTP_DETAILS, "/tmp", "Card/Music", unmatched=SYNCHRONIZE
        )
        sync.set_source_abs()
        sync.set_destination_abs()
        sync.handle_destination_dir_data(
            {
                "src_dir_abs": "/tmp/testdir",
                "dst_dir_fls": [
                    "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/song.mp3"  # noqa
                ],
                "dst_dir_abs": "/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir",  # noqa
            }
        )

        mock_copy_file.assert_called_once_with(
            dst_file="/tmp/testdir/song.mp3",
            src_file="/run/user/<user>/gvfs/mtp:host=%5Busb%3A002%2C003%5D/Card/Music/testdir/song.mp3",  # noqa
        )

    #
    # 'sync()'
    @patch.object(pysyncdroid.sync.Sync, "do_sync")
    @patch.object(pysyncdroid.sync.Sync, "get_sync_data")
    def test_sync_no_data(self, mock_get_sync_data, mock_do_sync):
        """
        Test 'sync' ends early if there are no files to synchronize.
        """
        mock_get_sync_data.return_value = [{"src_dir_fls": []}]

        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()
        sync.sync()

        mock_do_sync.assert_not_called()

    @patch.object(pysyncdroid.sync.Sync, "do_sync")
    @patch.object(pysyncdroid.sync.Sync, "get_sync_data")
    @patch.object(pysyncdroid.sync.Sync, "handle_destination_dir_data")
    def test_sync_ignore_unmatched(
        self,
        mock_handle_destination_dir_data,
        mock_get_sync_data,
        mock_do_sync,
    ):
        """
        Test 'sync' ignores unmatched files.
        """
        mock_get_sync_data.return_value = [FAKE_SYNC_DATA]

        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music")
        sync.set_source_abs()
        sync.set_destination_abs()
        sync.sync()

        mock_do_sync.assert_called_once_with(FAKE_SYNC_DATA)
        mock_handle_destination_dir_data.assert_not_called()

    @patch.object(pysyncdroid.sync.Sync, "do_sync")
    @patch.object(pysyncdroid.sync.Sync, "get_sync_data")
    @patch.object(pysyncdroid.sync.Sync, "handle_destination_dir_data")
    def test_sync_handle_unmatched(
        self,
        mock_handle_destination_dir_data,
        mock_get_sync_data,
        mock_do_sync,
    ):
        """
        Test 'sync' handles (removes, in this case) unmatched files.
        """
        mock_get_sync_data.return_value = [FAKE_SYNC_DATA]

        sync = Sync(FAKE_MTP_DETAILS, "/tmp", "Card/Music", unmatched=REMOVE)
        sync.set_source_abs()
        sync.set_destination_abs()
        sync.sync()

        mock_do_sync.assert_called_once_with(FAKE_SYNC_DATA)
        mock_handle_destination_dir_data.assert_called_once_with(
            FAKE_SYNC_DATA
        )
