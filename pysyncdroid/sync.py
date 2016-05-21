# -*- coding: utf-8 -*-


"""Synchronization class"""


import os

from pysyncdroid import gvfs
from pysyncdroid import exceptions
from pysyncdroid.utils import IGNORE, REMOVE, SYNCHRONIZE, readlink


class Sync(object):
    def __init__(self, mtp_details, source, destination,
                 unmatched=IGNORE, overwrite_existing=False,
                 verbose=False):
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
        :argument verbose: flag to display what is going on
        :type verbose: bool

        """
        self.mtp_url = mtp_details[0]
        self.mtp_gvfs_path = mtp_details[1]

        self.source = source
        self.source_abs = None
        self.destination = destination
        self.destination_abs = None

        self.verbose = verbose
        self.unmatched = unmatched
        self.overwrite_existing = overwrite_existing

    def _verbose(self, message):
        """
        Manage printing action messages, i.e. print what is going on if the
        'verbose' flag is set

        :argument message: message to print
        :type message: str

        """
        if self.verbose:
            print message

    def set_source_abs(self):
        """
        Create source directory absolute path.

        Make sure that the source exists and is a directory.

        First assume that computer is the source, then try the device.

        #NOTE: 1. implementation does not support path expansion
        #NOTE: 2. implementation supports only directory sync
        """
        source = readlink(self.source)

        for prefix in (os.getcwd(), self.mtp_gvfs_path):
            # Get absolute path for the specified source
            # Prepend prefix if given source is a relative path
            if not os.path.isabs(source):
                source_abs = os.path.join(prefix, source)
            else:
                source_abs = source

            if not os.path.exists(source_abs):
                continue

            if not os.path.isdir(source_abs):
                raise OSError('"{source}" is not a directory'
                              .format(source=source_abs))

            self.source_abs = source_abs
            break

        if self.source_abs is None:
            raise OSError('"{source}" does not exists on computer '
                          'neither on device'.format(source=source_abs))

    def set_destination_abs(self):
        """
        Create destination directory absolute path.

        #NOTE: implementation does not allow device only sync, i.e. that both
        #NOTE: source and destination are on the device
        """
        destination = readlink(self.destination)

        if self.source_abs is None:
            raise OSError('Source directory is not defined')

        if 'mtp:host' not in self.source_abs:
            # device is destination
            destination_abs = os.path.join(self.mtp_gvfs_path, destination)
        else:
            # computer is destination
            if not os.path.isabs(destination):
                destination_abs = os.path.join(os.getcwd(), destination)
            else:
                destination_abs = destination

        self.destination_abs = destination_abs

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
                raise

    def prepare_paths(self):
        """
        Prepare the list of files (and directories) that are about to be
        synchronized.

        :returns list

        """
        self._verbose('Gathering the list of files to synchronize, '
                      'this may take a while ...')

        to_sync = []

        for root, _, files in os.walk(self.source_abs):
            # skip directory without files, even if it contains a sub-directory
            # as sub-directories are walked later on
            if not files:
                continue

            rel_src_dir_pth = root.replace(self.source_abs, '')
            if rel_src_dir_pth:
                rel_src_dir_pth = rel_src_dir_pth.lstrip(os.sep)

            abs_dst_dir_pth = os.path.join(self.destination_abs, rel_src_dir_pth)  # NOQA

            current_dir = {}
            current_dir['abs_src_dir'] = root
            current_dir['abs_dst_dir'] = abs_dst_dir_pth
            current_dir['abs_fls_map'] = []

            for f in files:
                abs_src_f_pth = os.path.join(root, f)
                abs_dst_f_pth = os.path.join(abs_dst_dir_pth, f)

                src_2_dst = (abs_src_f_pth, abs_dst_f_pth)
                current_dir['abs_fls_map'].append(src_2_dst)

            to_sync.append(current_dir)

        return to_sync

    def sync(self):
        """
        Synchronize files.
        """
        for sync in self.prepare_paths():
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
                    self.source_abs, self.destination_abs = self.destination_abs, self.source_abs  # NOQA

                    # ignore everything but files synchronizing to source
                    self.unmatched = IGNORE
                    self.overwrite_existing = False

                    # do it
                    self.sync()
