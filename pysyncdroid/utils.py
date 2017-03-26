"""Shared functionality and constants"""


import os
import subprocess

from pysyncdroid.exceptions import BashException


#: constants
# unmatched files actions
IGNORE = 'ignore'
REMOVE = 'remove'
SYNCHRONIZE = 'synchronize'


def run_bash_cmd(cmd):
    """
    Run bash command.

    :argument cmd: bash command
    :type cmd: list

    :returns str

    """
    _cmd = ' '.join(cmd)

    try:
        bash_cmd = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

        out, err = bash_cmd.communicate()
        if err:
            exc_msg = ('Command "{cmd}" failed: {err}'
                       .format(cmd=_cmd, err=err))
            raise BashException(exc_msg)

        return out.strip()

    except OSError as exc:
        exc_msg = ('Error while trying to execute command "{cmd}": {exc}'
                   .format(cmd=_cmd, exc=exc.strerror))
        raise OSError(exc_msg)


def readlink(path):
    """
    A wrapper for the Linux `readlink` commmand.

    NOTE1: '-f' -> canonicalize by following path.
    NOTE2: `readlink` undestands '.', '..' and '/' and their combinations
    (e.g. './', '/..', '../').

    :argument path: path to resolve
    :type path: str

    :returns str
    """
    if not path:
        return path

    if path[0] == '~':
        path = os.path.expanduser(path)

    path = run_bash_cmd(['readlink', '-f', path]) or path

    if path != os.sep:
        path = path.rstrip(os.sep)

    return path
