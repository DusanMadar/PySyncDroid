"""Python wrappers for gvfs-tools bash commands"""


from pysyncdroid.utils import run_bash_cmd


def cp(src, dst):
    """
    cp

    :argument src: source file/directory to be copied
    :type src: str
    :argument dst: destination file/directory
    :type dst: str

    """
    run_bash_cmd(["gvfs-copy", src, dst])


def mkdir(path):
    """
    mkdir -p

    NOTE: '-p' -> Create parent directories when necessary.

    :argument path: new directory path
    :type path: str

    """
    run_bash_cmd(["gvfs-mkdir", "-p", path])


def mount(mtp_url):
    """
    mount

    :argument mtp_url: device MTP URL
    :type mtp_url: str

    """
    run_bash_cmd(["gvfs-mount", mtp_url])


def mv(src, dst):
    """
    mv

    :argument src: source file/directory to be copied
    :type src: str
    :argument dst: destination file/directory
    :type dst: str

    """
    cp(src, dst)
    rm(src)


def rm(src):
    """
    rm -f

    NOTE: '-f' -> Ignore nonexistent and non-deletable files.

    :argument src: file to be removed
    :type src: str

    """
    run_bash_cmd(["gvfs-rm", "-f", src])
