# -*- coding: utf-8 -*-


"""Synchronization class"""


import os

import pysyncdorid.utils_gvfs as gvfs


class Sync(object):
    def __init__(self, mtp, source, destination):
        """
        """
        self.mtp = mtp
        self.source = self._ensure_source(source)
        self.destination = os.path.join(mtp, destination)

        self.manage_unmatched = False
        self.overwrite_existing = False

    def _ensure_source(self, source):
        """
        Make sure that the source exists and is a directory.

        First assume that computer is the source, then try the device.

        :argument source: given synchronization source
        :type source: str

        :returns str

        """
        for prefix in (os.getcwd(), self.mtp):
            # Get absolute path for the specified source
            # Prepend prefix if given source is a relative path
            # TODO: add path expansion support
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

    def prepare_paths(self):
        """
        Prepare the list of files (and directories) that are about to be
        synchronized.

        :returns list

        """
        # ensure absolute paths
        # TODO: assuming computer is the source
        src_root = os.path.abspath(self.source)
        dst_root = os.path.join(self.mtp, self.destination)

        to_sync = []

        for root, _, files in os.walk(src_root):
            # skip directory without files, even if it contains a sub-directory
            # as sub-directories are walked later on
            if not files:
                continue

            rel_src_dir_pth = root.replace(src_root, '')
            if rel_src_dir_pth:
                rel_src_dir_pth = rel_src_dir_pth.lstrip(os.sep)

            abs_dst_dir_pth = os.path.join(dst_root, rel_src_dir_pth)

            current_dir = {}
            current_dir['rel_src_dir'] = rel_src_dir_pth
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

            # manage files that were already in the destination directory
            if parent_files:
                # TODO:
                pass
