"""Tests for utils functionality."""


import os
import unittest
from mock import Mock, patch

from pysyncdroid.exceptions import BashException
from pysyncdroid.utils import run_bash_cmd, readlink


class TestRunBashCmd(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('pysyncdroid.utils.subprocess.Popen')
        self.mock_popen = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def _mock_communicate(self, return_value):
        """
        Prepare 'Popen.communicate' response.

        :argument return_value: communicate return value
        :type return_value: tuple

        :returns Mock

        """
        process_mock = Mock()
        attrs = {'communicate.return_value': return_value}
        process_mock.configure_mock(**attrs)

        return process_mock

    def test_run_bash_cmd_output(self):
        """
        Test 'run_bash_cmd' returns an expected output for a valid command.
        """
        self.mock_popen.return_value = self._mock_communicate(('a', ''))

        out = run_bash_cmd(['echo', 'a'])
        self.assertEqual(out, 'a')

    def test_run_bash_cmd_oserror(self):
        """
        Test 'run_bash_cmd' raises an OSError when trying to execute a
        non-existent file.
        """
        self.mock_popen.side_effect = OSError
        with self.assertRaises(OSError) as exc:
            run_bash_cmd(['no_command'])

        err_msg = 'Error while trying to execute command "no_command": None'
        self.assertEqual(str(exc.exception), err_msg)

    def test_run_bash_cmd_bashexception(self):
        """
        Test 'run_bash_cmd' raises a BashException when trying to execute a
        command in a non-standard way (with missing argument in this case).
        """
        lsub_msg = 'lsusb: option requires an argument -- "d"'
        self.mock_popen.return_value = self._mock_communicate(('', lsub_msg))

        with self.assertRaises(BashException) as exc:
            run_bash_cmd(['lsusb', '-d'])

        err_msg = 'Command "lsusb -d" failed: {}'.format(lsub_msg)
        self.assertEqual(str(exc.exception), err_msg)


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

    @patch('pysyncdroid.utils.os.path.expanduser')
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

    def test_readlink_slash_trailing(self):
        """
        Test 'readlink' strips trailing '/'.
        """
        self.mock_run_bash_cmd.return_value = '/tmp/example/'
        self.assertEqual(readlink('/tmp/example/'), '/tmp/example')

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


if __name__ == '__main__':
    unittest.main()
