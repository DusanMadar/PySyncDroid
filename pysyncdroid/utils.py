"""Shared functionality and constants"""


import subprocess

from pysyncdorid.exceptions import BashException


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
