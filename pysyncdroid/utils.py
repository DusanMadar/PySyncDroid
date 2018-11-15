"""Shared functionality and constants"""


import subprocess

from pysyncdroid.exceptions import BashException


def run_bash_cmd(cmd):
    """
    Run bash command.

    :argument cmd: bash command
    :type cmd: list

    :returns str

    """
    _cmd = " ".join(cmd)

    try:
        bash_cmd = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        out, err = bash_cmd.communicate()
        if err:
            try:
                err = err.decode("utf-8")
            except AttributeError:
                pass

            # TODO use `gio` over `gvfs-*`.
            # This started to manifest on Ubuntu 18.04.
            if not err.startswith("This tool has been deprecated"):
                exc_msg = 'Command "{cmd}" failed: {err}'.format(
                    cmd=_cmd, err=err
                )
                raise BashException(exc_msg)

        try:
            out = out.decode("utf-8")
        except AttributeError:
            pass

        return out.strip()

    except OSError as exc:
        exc_msg = 'Error while trying to execute command "{cmd}": {exc}'.format(
            cmd=_cmd, exc=exc.strerror
        )
        raise OSError(exc_msg)
