# -*- coding: utf-8 -*-


"""Main synchronization functionality."""


from __future__ import print_function

import os

from pysyncdroid import exceptions
from pysyncdroid import gvfs
from pysyncdroid.utils import IGNORE, REMOVE, SYNCHRONIZE, run_bash_cmd


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

    if path[0] == '~':
        path = os.path.expanduser(path)

    path = run_bash_cmd(['readlink', '-f', path]) or path

    return path


class Sync(object):
    def __init__(self, mtp_details, source, destination,
                 unmatched=IGNORE, overwrite_existing=False,
                 ignore_file_types=None, verbose=False):
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
            exc_msg = exc.message.strip()

            if exc_msg.endswith('Connection reset by peer'):
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

        if not source_abs_exists:
            raise OSError(
                '"{source}" does not exist on computer or on device.'
                .format(source=self.source)
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

        if 'mtp:host' in self.source:
            # computer is destination
            destination_abs = destination
        else:
            # device is destination
            destination_abs = os.path.join(self.mtp_gvfs_path, destination)

        self.destination = destination_abs

    def set_destination_subdir_abs(self, src_subdir_abs):
        """
        Create destination sub-directory absolute path.

        :argument src_subdir_abs: source sub directory absolute path
        :type src_subdir_abs: str

        :returns str

        """
        rel_src_subdir_pth = src_subdir_abs.replace(self.source, '')
        if rel_src_subdir_pth:
            # strip leading slashes (if any) to avoid confusing 'os.path.join'
            # (i.e. passing an absolute path as the second argument)
            # https://docs.python.org/3/library/os.path.html#os.path.join
            rel_src_subdir_pth = rel_src_subdir_pth.lstrip(os.sep)

        return os.path.join(self.destination, rel_src_subdir_pth)

    def subdir_template(self, src_subdir_abs):
        """
        Prepare sub-directory dict.

        :argument src_subdir_abs: source sub directory absolute path
        :type src_subdir_abs: str

        :returns dict

        """
        dst_subdir_abs = self.set_destination_subdir_abs(src_subdir_abs)

        subdir = {}
        subdir['abs_src_dir'] = src_subdir_abs
        subdir['abs_dst_dir'] = dst_subdir_abs
        subdir['abs_fls_map'] = []

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
                extension = extension.lower().replace('.', '')

                if extension in self.ignore_file_types:
                    raise exceptions.IgnoredTypeException

    def collect_subdir_data(self, src_subdir_abs, src_subdir_files):
        """
        Collect sub-directory content to synchronize.

        :argument src_subdir_abs: source sub-directory absolute path
        :type src_subdir_abs: str
        :argument src_subdir_files: sub-directory files
        :type src_subdir_files: list

        :returns dict

        """
        subdir = self.subdir_template(src_subdir_abs)

        for f in src_subdir_files:
            try:
                self.handle_ignored_file_type(f)
            except exceptions.IgnoredTypeException:
                continue

            # append absolute paths
            abs_src_f_pth = os.path.join(subdir['abs_src_dir'], f)
            abs_dst_f_pth = os.path.join(subdir['abs_dst_dir'], f)

            src_2_dst = (abs_src_f_pth, abs_dst_f_pth)
            subdir['abs_fls_map'].append(src_2_dst)

        return subdir

    def prepare_paths(self):
        """
        Prepare the list of files (and directories) that are about to be
        synchronized.

        :returns list

        """
        self._verbose('Gathering the list of files to synchronize, '
                      'this may take a while ...')

        to_sync = []

        for root, _, files in os.walk(self.source):
            # skip directory without files, even if it contains a sub-directory
            # as sub-directories are walked later on
            if not files:
                continue

            subdir_data = self.collect_subdir_data(root, files)
            to_sync.append(subdir_data)

        return to_sync

    def sync(self):
        """
        Synchronize files.
        """
        for sync in self.prepare_paths():
            if not sync['abs_fls_map']:
                self._verbose('No files to sync')
                return

            parent_dir = sync['abs_dst_dir']

            # ensure parent directory tree
            if not os.path.exists(parent_dir):
                self._verbose('Creating directory {d}'.format(d=parent_dir))
                self.gvfs_wrapper(gvfs.mkdir, parent_dir)

            # get already existing files if any
            parent_files = set([os.path.join(parent_dir, f)
                                for f in os.listdir(parent_dir)])

            for src, dst in sync['abs_fls_map']:
                if dst in parent_files:
                    parent_files.remove(dst)

                    # ignore existing files
                    if not self.overwrite_existing:
                        continue

                self._verbose('Copying {s} to {d}'.format(s=src, d=dst))
                self.gvfs_wrapper(gvfs.cp, src, dst)

            # skip any other actions is unmatched files are ignored
            if self.unmatched == IGNORE:
                continue

            # manage files that were already in the destination directory
            # but are missing in the source directory
            for unmatched_file in parent_files:
                if self.unmatched == REMOVE:
                    self._verbose('Removing {u}'.format(u=unmatched_file))
                    self.gvfs_wrapper(gvfs.rm, unmatched_file)

                elif self.unmatched == SYNCHRONIZE:
                    # revert the synchronization
                    self.source, self.destination = self.destination, self.source  # NOQA

                    # ignore everything but files synchronizing to source
                    self.unmatched = IGNORE
                    self.overwrite_existing = False

                    # do it
                    self.sync()
