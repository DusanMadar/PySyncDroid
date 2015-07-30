#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""PySyncDroid Command Line Interface (CLI)"""


import argparse

from pysyncdorid import sync
from pysyncdorid import find_device


parser = argparse.ArgumentParser()

# device info
parser.add_argument('-V', '--vendor', required=True,
                    help='Device vendor name')
parser.add_argument('-M', '--model', required=True,
                    help='Device model name')

# content info
parser.add_argument('-s', '--source', required=True,
                    help='Source directory')
parser.add_argument('-d', '--destination', required=True,
                    help='Destination directory')

# optional arguments
parser.add_argument('-c', '--clear_parent', action='store_true', default=False,
                    help='Flag to clear destination content')
parser.add_argument('-o', '--overwrite', action='store_true', default=False,
                    help='Flag to overwrite existing files')


if __name__ == '__main__':
    args = parser.parse_args()

    usb_bus, device = find_device.connection_details(vendor=args.vendor,
                                                     model=args.model)
    mtp = find_device.get_mtp_path(usb_bus, device)

    sync = sync(mtp=mtp, source=args.source, destination=args.destination)
    sync.sync()
