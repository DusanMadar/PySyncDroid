#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""PySyncDroid Command Line Interface (CLI)"""


import argparse

from pysyncdroid.sync import Sync
from pysyncdroid import find_device
from pysyncdroid.utils import IGNORE, REMOVE, SYNCHRONIZE


parser = argparse.ArgumentParser()

# device info
parser.add_argument('-V', '--vendor', required=True,
                    help='Device vendor name')
parser.add_argument('-M', '--model', required=True,
                    help='Device model name')

# sync info
parser.add_argument('-s', '--source', required=True,
                    help='Source directory')
parser.add_argument('-d', '--destination', required=True,
                    help='Destination directory')

# optional arguments
parser.add_argument('-v', '--verbose', action='store_true', default=False,
                    help='Display actions; not used by default')
parser.add_argument('-u', '--unmatched', choices=[IGNORE, REMOVE, SYNCHRONIZE],
                    help='Unmatched files action; ignoring by default',
                    default=IGNORE)
parser.add_argument('-o', '--overwrite', action='store_true', default=False,
                    help='Overwrite existing files; not used by default')


def main():
    args = parser.parse_args()

    usb_bus, device = find_device.get_connection_details(vendor=args.vendor,
                                                         model=args.model)
    mtp_details = find_device.get_mtp_details(usb_bus, device)

    sync = Sync(mtp_details=mtp_details,
                source=args.source, destination=args.destination,
                unmatched=args.unmatched, overwrite_existing=args.overwrite,
                verbose=args.verbose)
    sync.sync()


if __name__ == '__main__':
    main()
