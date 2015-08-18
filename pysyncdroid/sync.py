# -*- coding: utf-8 -*-


"""Synchronization class"""


import os

import pysyncdroid.gvfs as gvfs

from pysyncdroid.utils import IGNORE, REMOVE, SYNCHRONIZE


class Sync(object):
    def __init__(self, mtp, source, destination,
                 unmatched=IGNORE, overwrite_existing=False):
        """
        Class for synchronizing directories between a computer and an Android
        device or vice versa.

        :argument mtp: path to the MTP connected device
        :type mtp: str
        :argument source: path to the sync source directory
        :type source: str
        :argument destination: path to the sync destination directory
        :type destination: str
        :argument unmatched: unmatched files action
        :type unmatched: str
        :argument overwrite_existing: flag to overwrite existing files
        :type overwrite_existing: bool

        """
        self.mtp = mtp
        self.source = self._get_source_abs(source)
        self.destination = self._get_destination_abs(destination)

        self.unmatched = unmatched
        self.overwrite_existing = overwrite_existing

    def _get_source_abs(self, source):
        """
        Create source directory absolute path.

        Make sure that the source exists and is a directory.

        First assume that computer is the source, then try the device.

        #NOTE: 1. implementation does not support path expansion
        #NOTE: 2. implementation supports only directory sync

        :argument source: synchronization source
        :type source: str

        :returns str

        """
        for prefix in (os.getcwd(), self.mtp):
            # Get absolute path for the specified source
            # Prepend prefix if given source is a relative path
            if not os.path.isabs(source):
                abs_source = os.path.join(prefix, source)
            else:
                abs_source = source

            if not os.path.exists(abs_source):
                continue

            if not os.path.isdir(abs_source):
                raise OSError('"{source}" is not a directory'
                              .format(source=abs_source))

            return abs_source

        raise OSError('"{source}" does not exists on computer '
                      'neither on device'.format(source=abs_source))

    def _get_destination_abs(self, destination):
        """
        Create destination directory absolute path.

        #NOTE: implementation does not allow device only sync, i.e. that both
        #NOTE: source and destination are on the device

        :argument destination: synchronization destination
        :type destination: str

        :returns str

        """
        if 'mtp:host' not in self.source:
            # device is destination
            abs_destination = os.path.join(self.mtp, destination)
        else:
            # computer is destination
            if not os.path.isabs(destination):
                abs_destination = os.path.join(os.getcwd(), destination)
            else:
                abs_destination = destination

        return abs_destination

    def prepare_paths(self):
        """
        Prepare the list of files (and directories) that are about to be
        synchronized.

        :returns list

        """
        to_sync = []

        for root, _, files in os.walk(self.source):
            # skip directory without files, even if it contains a sub-directory
            # as sub-directories are walked later on
            if not files:
                continue

            rel_src_dir_pth = root.replace(self.source, '')
            if rel_src_dir_pth:
                rel_src_dir_pth = rel_src_dir_pth.lstrip(os.sep)

            abs_dst_dir_pth = os.path.join(self.destination, rel_src_dir_pth)

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
                gvfs.mkdir(parent_dir)

            # get already existing files if any
            parent_files = set([os.path.join(parent_dir, f)
                                for f in os.listdir(parent_dir)])

            for src, dst in sync['abs_fls_map']:
                if dst in parent_files:
                    parent_files.remove(dst)

                    # ignore existing files
                    if not self.overwrite_existing:
                        continue

                gvfs.cp(src, dst)

            # skip any other actions is unmatched files are ignored
            if self.unmatched == IGNORE:
                continue

            # manage files that were already in the destination directory
            # but are missing in the source directory
            for unmatched_file in parent_files:
                if self.unmatched == REMOVE:
                    gvfs.rm(unmatched_file)

                elif self.unmatched == SYNCHRONIZE:
                    # revert the synchronization
                    self.source, self.destination = self.destination, self.source  # NOQA

                    # ignore everything but files synchronizing to source
                    self.unmatched = IGNORE
                    self.overwrite_existing = False

                    # do it
                    self.sync()
