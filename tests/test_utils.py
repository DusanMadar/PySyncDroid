"""Tests for utils functionality."""


import unittest
from unittest.mock import Mock, patch

from pysyncdroid.exceptions import BashException
from pysyncdroid.utils import run_bash_cmd


class TestRunBashCmd(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("pysyncdroid.utils.subprocess.Popen")
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
        attrs = {"communicate.return_value": return_value}
        process_mock.configure_mock(**attrs)

        return process_mock

    def test_run_bash_cmd_output(self):
        """
        Test 'run_bash_cmd' returns an expected output for a valid command.
        """
        self.mock_popen.return_value = self._mock_communicate(("a", ""))

        out = run_bash_cmd(["echo", "a"])
        self.assertEqual(out, "a")

    def test_run_bash_cmd_oserror(self):
        """
        Test 'run_bash_cmd' raises an OSError when trying to execute a
        non-existent file.
        """
        self.mock_popen.side_effect = OSError
        with self.assertRaises(OSError) as exc:
            run_bash_cmd(["no_command"])

        err_msg = 'Error while trying to execute command "no_command": None'
        self.assertEqual(str(exc.exception), err_msg)

    def test_run_bash_cmd_bashexception(self):
        """
        Test 'run_bash_cmd' raises a BashException when trying to execute a
        command in a non-standard way (with missing argument in this case).
        """
        lsub_msg = 'lsusb: option requires an argument -- "d"'
        self.mock_popen.return_value = self._mock_communicate(("", lsub_msg))

        with self.assertRaises(BashException) as exc:
            run_bash_cmd(["lsusb", "-d"])

        err_msg = 'Command "lsusb -d" failed: {}'.format(lsub_msg)
        self.assertEqual(str(exc.exception), err_msg)
