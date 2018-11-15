#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""PySyncDroid Command Line Interface (CLI)"""


import argparse

from pysyncdroid.exceptions import DeviceException, MappingFileException
from pysyncdroid.find_device import get_connection_details, get_mtp_details
from pysyncdroid.sync import Sync, IGNORE, REMOVE, SYNCHRONIZE


parser = argparse.ArgumentParser()

# device info
parser.add_argument("-V", "--vendor", required=True, help="Device vendor name")
parser.add_argument("-M", "--model", required=True, help="Device model name")

# sync info
parser.add_argument("-s", "--source", help="Source directory")
parser.add_argument("-d", "--destination", help="Destination directory")
parser.add_argument(
    "-f", "--file", help="Source to destination mapping file absolute path"
)

# optional arguments
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    default=False,
    help="Display actions; not used by default",
)
parser.add_argument(
    "-u",
    "--unmatched",
    choices=[IGNORE, REMOVE, SYNCHRONIZE],
    help="Unmatched files action; ignoring by default",
    default=IGNORE,
)
parser.add_argument(
    "-o",
    "--overwrite",
    action="store_true",
    default=False,
    help="Overwrite existing files; not used by default",
)
parser.add_argument(
    "-i",
    "--ignore-file-type",
    nargs="+",
    default=None,
    help="Ignored file type(s), e.g. html, txt, ...",
)


def parse_sync_mapping_file(sync_mapping_file, sources, destinations):
    """
    Parse sync mapping file.

    :argument sync_mapping_file: Sync mapping file absolute path
    :type sync_mapping_file: str
    :argument sources: list of sources
    :type sources: list
    :argument destinations: list of destinations
    :type destinations: list

    """
    with open(sync_mapping_file, "r") as f:
        mapping_lines = f.readlines()

    for line in mapping_lines:
        line = line.replace("\n", "")
        if not line:
            continue

        source, destination = line.split("==>")
        if not source or not destination:
            raise MappingFileException(
                "Please separate source and destination"
                'with "==>".\n'
                'Problematic line: "{}"'.format(line)
            )

        sources.append(source)
        destinations.append(destination)


def parse_sync_info(args):
    """
    Parse sync info, i.e. handle combinations of soure, destination and file
    arguments.

    :argument args: command line arguments namespace
    :type args: object

    :returns tuple

    """
    sources = []
    destinations = []

    if args.file is None:
        # no sync info supplied (none of source, destination, file)
        if args.source is None or args.destination is None:
            raise argparse.ArgumentError(
                None,
                "Either sync mapping file (-f) or source (-s) and destination "
                "(-d) must be defined.",
            )

        sources.append(args.source)
        destinations.append(args.destination)

    else:
        # when syncing from file, source and destination cannot be set
        if args.source is not None or args.destination is not None:
            raise argparse.ArgumentError(
                None,
                "Source (-s) and destination (-d) cannot be set when syncing "
                "from file (-f).",
            )

        parse_sync_mapping_file(args.file, sources, destinations)

    return sources, destinations


def main():
    args = parser.parse_args()

    try:
        usb_bus_id, device_id = get_connection_details(args.vendor, args.model)
        mtp_details = get_mtp_details(usb_bus_id, device_id)
    except DeviceException as exc:
        return exc.message

    try:
        sources, destinations = parse_sync_info(args)
    except (argparse.ArgumentError, MappingFileException) as exc:
        return exc.message

    for source, destination in zip(sources, destinations):
        source = source.strip()
        destination = destination.strip()

        sync = Sync(
            mtp_details=mtp_details,
            source=source,
            destination=destination,
            verbose=args.verbose,
            unmatched=args.unmatched,
            overwrite_existing=args.overwrite,
            ignore_file_types=args.ignore_file_type,
        )

        sync.set_source_abs()
        sync.set_destination_abs()

        sync.sync()


if __name__ == "__main__":
    main()
