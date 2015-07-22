"""Tests for utils functionality"""


import pytest

from pysyncdorid.utils import run_bash_cmd
from pysyncdorid.exceptions import BashException


def test_run_bash_cmd_oserror():
    """
    Test if run_bash_cmd raises an OSError when trying to execute a
    non-existent file.
    """
    with pytest.raises(OSError):
        run_bash_cmd(['no_command'])


def test_run_bash_cmd_bashexception():
    """
    Test if run_bash_cmd raises a BashException when trying to execute a
    command in a non-standard way.
    """
    with pytest.raises(BashException):
        run_bash_cmd(['lsusb', '-d'])


def test_run_bash_cmd_expected_output():
    """
    Test if run_bash_cmd returns an expected output for a valid command.
    """
    assert run_bash_cmd(['whoami']) == 'dm'
