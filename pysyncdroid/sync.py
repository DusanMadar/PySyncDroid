# -*- coding: utf-8 -*-


"""Main synchronization functionality."""


import os

from pysyncdroid import exceptions
from pysyncdroid import gvfs
from pysyncdroid.utils import run_bash_cmd


#: constants
# unmatched files actions
IGNORE = "ignore"
REMOVE = "remove"
SYNCHRONIZE = "synchronize"


def readlink(path):
    """
    A wrapper for the Linux `readlink` commmand.

    NOTE1: '-f' -> canonicalize by following path.
    NOTE2: `readlink` undestands '.', '..' and '/' and their combinations
    (e.g. './', '/..', '../').
    NOTE3: `readlink` strips trailing slashes by default.

    :argument path: path to resolve
    :type path: str

    :returns str
    """
    if not path:
        return path

    if path[0] == "~":
        path = os.path.expanduser(path)

    return run_bash_cmd(["readlink", "-f", path]) or path


class Sync(object):
    def __init__(
        self,
        mtp_details,
        source,
        destination,
        unmatched=IGNORE,
        overwrite_existing=False,
        ignore_file_types=None,
        verbose=False,
    ):
        """
        Class for synchronizing directories between a computer and an Android
        device or vice versa.

        :argument mtp_details: MTP URL and gvfs path to the device
        :type mtp_details: tuple
        :argument source: path to the sync source directory
        :type source: str
        :argument destination: path to the sync destination directory
        :type destination: str
        :argument unmatched: unmatched files action
        :type unmatched: str
        :argument overwrite_existing: flag to overwrite existing files
        :type overwrite_existing: bool
        :argument ignore_file_types: extensions for ignored file types
        :type ignore_file_types: list ot None
        :argument verbose: flag to display what is going on
        :type verbose: bool

        """
        self.mtp_url = mtp_details[0]
        self.mtp_gvfs_path = mtp_details[1]

        self.source = source
        self.destination = destination

        self.verbose = verbose
        self.unmatched = unmatched
        self.overwrite_existing = overwrite_existing

        if ignore_file_types is not None:
            ignore_file_types = [f.lower() for f in ignore_file_types]
        self.ignore_file_types = ignore_file_types

    def _verbose(self, message):
        """
        Manage printing action messages, i.e. print what is going on if the
        'verbose' flag is set.

        :argument message: message to print
        :type message: str

        """
        if self.verbose:
            print(message)

    def gvfs_wrapper(self, func, *args):
        """
        Wrap gvfs operations and handle exceptions which can terminate
        processing.

        Currently handling:
            Connection reset by peer

        :argument func: gvfs function to be executed
        :type func: function
        :argument *args: function's arguments
        :type *args:

        """
        try:
            func(*args)
        except exceptions.BashException as exc:
            exc_msg = str(exc).strip()

            if exc_msg.endswith("Connection reset by peer"):
                # re-mount and try again
                gvfs.mount(self.mtp_url)
                func(*args)
            else:
                raise exc

    def set_source_abs(self):
        """
        Create source directory absolute path.

        Make sure that the source exists and is a directory.

        First assume that computer is the source, then try the device.

        NOTE1: implementation does not support path expansion.
        NOTE2: implementation supports only directory sync.
        """
        source = readlink(self.source)
        source_abs_exists = False

        for prefix in (os.getcwd(), self.mtp_gvfs_path):
            # Get absolute path for the specified source
            # Prepend prefix if given source is a relative path
            if not os.path.isabs(source):
                source_abs = os.path.join(prefix, source)
            else:
                source_abs = source

            source_abs_exists = os.path.exists(source_abs)
            if source_abs_exists:
                break

        try:
            source_abs = source_abs.decode("utf-8")
        except AttributeError:
            pass

        if not source_abs_exists:
            raise OSError(
                '"{source}" does not exist on computer or on device.'.format(
                    source=self.source
                )
            )
        elif not os.path.isdir(source_abs):
            raise OSError(
                '"{source}" is not a directory.'.format(source=source_abs)
            )

        self.source = source_abs

    def set_destination_abs(self):
        """
        Create destination directory absolute path.

        NOTE1: implementation does not allow device only sync, i.e. that both
        source and destination are on the device.
        NOTE2: it's assumed that source is defined.
        NOTE3: no need to check if destination exists or is a dir - it will be
        created if necessary.
        """
        destination = readlink(self.destination)

        if "mtp:host" in self.source:
            # computer is destination
            destination_abs = destination
        else:
            # device is destination
            destination_abs = os.path.join(self.mtp_gvfs_path, destination)

        try:
            destination_abs = destination_abs.decode("utf-8")
        except AttributeError:
            pass

        self.destination = destination_abs

    def set_destination_subdir_abs(self, src_subdir_abs):
        """
        Create destination subdir absolute path.

        :argument src_subdir_abs: source sub directory absolute path
        :type src_subdir_abs: str

        :returns str

        """
        rel_src_subdir_pth = src_subdir_abs.replace(self.source, "")
        if rel_src_subdir_pth:
            # strip leading slashes (if any) to avoid confusing 'os.path.join'
            # (i.e. passing an absolute path as the second argument)
            # https://docs.python.org/3/library/os.path.html#os.path.join
            rel_src_subdir_pth = rel_src_subdir_pth.lstrip(os.sep)

        return os.path.join(self.destination, rel_src_subdir_pth)

    def sync_data_template(self, src_subdir_abs, dst_subdir_abs):
        """
        Prepare sync data dict.

        :argument src_subdir_abs: source subdir absolute path
        :type src_subdir_abs: str
        :argument dst_subdir_abs: destination subdir absolute path
        :type dst_subdir_abs: str

        :returns dict

        """
        subdir = {}

        subdir["src_dir_abs"] = src_subdir_abs.rstrip("/")
        subdir["dst_dir_abs"] = dst_subdir_abs.rstrip("/")

        # list of files to be synced
        subdir["src_dir_fls"] = []
        # list of files present in the destination directory prior to sync
        subdir["dst_dir_fls"] = []

        return subdir

    def handle_ignored_file_type(self, path):
        """
        Check if a given file is allowed to be synchronized.

        :argument path: file path
        :type path: str

        """
        if self.ignore_file_types:
            _, extension = os.path.splitext(path)

            if extension:
                extension = extension.lower().replace(".", "")

                if extension in self.ignore_file_types:
                    raise exceptions.IgnoredTypeException

    def get_source_subdir_data(self, src_subdir_files, sync_data):
        """
        Collect source subdir content to synchronize.

        :argument src_subdir_files: source subdir filenames
        :type src_subdir_files: list
        :argument sync_data: sync data dictionary
        :type sync_data: dict

        """
        for f in src_subdir_files:
            try:
                self.handle_ignored_file_type(f)
            except exceptions.IgnoredTypeException:
                continue

            src_f_abs = os.path.join(sync_data["src_dir_abs"], f)
            sync_data["src_dir_fls"].append(src_f_abs)

    def get_destination_subdir_data(self, sync_data):
        """
        Collect destination subdir content, i.e. files present in the dst
        subdir prior to sync. We refere to these files as to 'unmatched' files.

        If the destination subdir doesn't exist, create it.

        :argument sync_data: sync data dictionary
        :type sync_data: dict

        """
        if not os.path.exists(sync_data["dst_dir_abs"]):
            # ensure destination dir tree
            self._verbose(
                "Creating directory {d}".format(d=sync_data["dst_dir_abs"])
            )
            self.gvfs_wrapper(gvfs.mkdir, sync_data["dst_dir_abs"])
        else:
            # get already existing files in the destination dir if any
            for f in os.listdir(sync_data["dst_dir_abs"]):
                try:
                    self.handle_ignored_file_type(f)
                except exceptions.IgnoredTypeException:
                    continue

                dst_f_abs = os.path.join(sync_data["dst_dir_abs"], f)
                sync_data["dst_dir_fls"].append(dst_f_abs)

    def get_sync_data(self):
        """
        Get list of sync data dictionaries describing files (and directories)
        that are about to be synchronized.

        :returns list

        """
        self._verbose(
            'Gathering list of files to synchronize in "{s}", '
            "this may take a while ...".format(s=self.source)
        )

        sync_data_set = []

        for root, _, files in os.walk(self.source):
            # skip directory without files, even if it contains a subdir as
            # subdirs are walked on later
            if not files:
                continue

            # create the sync data dict for this subdir
            src_subdir_abs = root
            dst_subdir_abs = self.set_destination_subdir_abs(src_subdir_abs)
            sync_data = self.sync_data_template(src_subdir_abs, dst_subdir_abs)

            # get files in both source and destination directory
            self.get_source_subdir_data(files, sync_data)
            self.get_destination_subdir_data(sync_data)

            sync_data_set.append(sync_data)

        return sync_data_set

    def copy_file(self, src_file, dst_file):
        """
        Copy file from src to dst.

        :argument src_file: source file absolute path
        :type src_file: str
        :argument dst_file: destination file absolute path
        :type dst_file: str

        """
        self._verbose("Copying {s} to {d}".format(s=src_file, d=dst_file))
        self.gvfs_wrapper(gvfs.cp, src_file, dst_file)

    def do_sync(self, sync_data):
        """
        Iterate over source dir files and copy then to the given destination.
        While doing so, update the list of destinatin files.

        :argument sync_data: sync data dictionary
        :type sync_data: dict

        """
        for src_file in sync_data["src_dir_fls"]:
            dst_file = src_file.replace(
                sync_data["src_dir_abs"], sync_data["dst_dir_abs"]
            )

            if (
                sync_data["dst_dir_fls"]
                and dst_file in sync_data["dst_dir_fls"]
            ):
                sync_data["dst_dir_fls"].remove(dst_file)

                # ignore existing files
                if not self.overwrite_existing:
                    continue

            self.copy_file(src_file, dst_file)

    def handle_destination_dir_data(self, sync_data):
        """
        Manage files that were already in the destination directory but are
        missing in the source directory (i.e. 'unmatched' files).

        :argument sync_data: sync data dictionary
        :type sync_data: dict

        """
        # end early if there were no files in the destination directory
        if not sync_data["dst_dir_fls"]:
            return

        for unmatched_file in sync_data["dst_dir_fls"]:
            if self.unmatched == REMOVE:
                self._verbose("Removing {u}".format(u=unmatched_file))
                self.gvfs_wrapper(gvfs.rm, unmatched_file)

            elif self.unmatched == SYNCHRONIZE:
                dst_file = unmatched_file.replace(
                    sync_data["dst_dir_abs"], sync_data["src_dir_abs"]
                )
                self.copy_file(src_file=unmatched_file, dst_file=dst_file)

    def sync(self):
        """
        Synchronize files.
        """
        for sync_data in self.get_sync_data():
            if not sync_data["src_dir_fls"]:
                self._verbose("No files to sync")
                return

            self.do_sync(sync_data)

            # skip any other actions if unmatched files are ignored
            if self.unmatched == IGNORE:
                continue

            self.handle_destination_dir_data(sync_data)
