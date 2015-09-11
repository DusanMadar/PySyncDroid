"""Tests for utils functionality"""


import os
import pytest
import getpass

from pysyncdroid.exceptions import BashException
from pysyncdroid.utils import run_bash_cmd, readlink


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


def test_readlink():
    """
    Test if the auxiliary `readlink` function works as expected.
    """
    assert readlink('') == ''
    assert readlink('.') == os.getcwd()
    assert readlink('..') == os.path.dirname(os.getcwd())
    assert readlink('/..') == os.sep
    assert readlink('./') == os.getcwd()
    assert readlink('../') == os.path.dirname(os.getcwd())
    assert readlink(os.sep) == os.sep
    assert readlink('~') == '/home/{user}'.format(user=getpass.getuser())
    assert readlink('~/..') == '/home'
    assert readlink('../../..') == '/home'
    phone_card = 'Phone/Card'
    assert readlink(phone_card) == phone_card
    nonexisting = 'nonexisting_path'
    assert readlink(nonexisting) == os.path.join(os.getcwd(), nonexisting)
