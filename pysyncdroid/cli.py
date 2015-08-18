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
parser.add_argument('-u', '--unmatched', choices=[IGNORE, REMOVE, SYNCHRONIZE],
                    help='Unmatched files action', default=IGNORE)
parser.add_argument('-o', '--overwrite', action='store_true', default=False,
                    help='Flag to overwrite existing files')


def main():
    args = parser.parse_args()

    usb_bus, device = find_device.connection_details(vendor=args.vendor,
                                                     model=args.model)
    mtp = find_device.get_mtp_path(usb_bus, device)

    sync = Sync(mtp=mtp, source=args.source, destination=args.destination,
                unmatched=args.unmatched, overwrite_existing=args.overwrite)
    sync.sync()


if __name__ == '__main__':
    main()
