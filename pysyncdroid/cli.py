#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""PySyncDroid Command Line Interface (CLI)"""


import argparse

from pysyncdroid import find_device
from pysyncdroid.sync import Sync
from pysyncdroid.utils import IGNORE, REMOVE, SYNCHRONIZE


parser = argparse.ArgumentParser()

# device info
parser.add_argument('-V', '--vendor', required=True,
                    help='Device vendor name')
parser.add_argument('-M', '--model', required=True,
                    help='Device model name')

# sync info
parser.add_argument('-s', '--source', help='Source directory')
parser.add_argument('-d', '--destination', help='Destination directory')
parser.add_argument('-f', '--file',
                    help='Source to destination mapping file absolute path')

# optional arguments
parser.add_argument('-v', '--verbose', action='store_true', default=False,
                    help='Display actions; not used by default')
parser.add_argument('-u', '--unmatched', choices=[IGNORE, REMOVE, SYNCHRONIZE],
                    help='Unmatched files action; ignoring by default',
                    default=IGNORE)
parser.add_argument('-o', '--overwrite', action='store_true', default=False,
                    help='Overwrite existing files; not used by default')
parser.add_argument('-i', '--ignore-file-type', nargs='+', default=None,
                    help='Ignored file type(s), e.g. html, txt, ...')


def main():
    sources = []
    destinations = []

    args = parser.parse_args()

    # no sync info supplied (none of source, destination, file)
    if args.file is None:
        if args.source is None or args.destination is None:
            return ('Either mapping file or a combination of '
                    'source and destination must be defined.')

        sources.append(args.source)
        destinations.append(args.destination)

    # when syncing from file, source and destination cannot be set
    else:
        if args.source is not None or args.destination is not None:
            return ('Source and destination cannot be set when '
                    'syncing from a file.')

        with open(args.file, 'r') as f:
            mapping_lines = f.readlines()

        for line in mapping_lines:
            line = line.replace('\n', '')
            line_parts = line.split('==>')

            sources.append(line_parts[0])
            destinations.append(line_parts[1])

    usb_bus, device = find_device.get_connection_details(vendor=args.vendor,
                                                         model=args.model)
    mtp_details = find_device.get_mtp_details(usb_bus, device)

    for source, destination in zip(sources, destinations):
        sync = Sync(mtp_details=mtp_details,
                    source=source, destination=destination,
                    unmatched=args.unmatched, overwrite_existing=args.overwrite,
                    verbose=args.verbose, ignore_file_types=args.ignore_file_type)  # noqa

        sync.set_source_abs()
        sync.set_destination_abs()

    sync.sync()


if __name__ == '__main__':
    main()
