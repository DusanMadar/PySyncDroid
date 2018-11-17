from argparse import ArgumentError
import getpass
from io import StringIO
import os
import pwd
import sys
import tempfile
import unittest
from unittest.mock import patch

from pysyncdroid import cli
from pysyncdroid.exceptions import MappingFileException


class TestCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = cli.create_parser()

    @patch("sys.stderr", new=StringIO())
    def test_parser_no_args(self):
        """
        Test it's not possible to run pysyncdroid without arguments.
        """
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])

    def test_parser(self):
        """
        Test required arguments cannot be skipped.
        """
        cmd = "-M model -V vendor".split(" ")
        args = self.parser.parse_args(cmd)
        self.assertEqual(
            str(args),
            "Namespace(destination=None, file=None, ignore_file_type=None, "
            "model='model', overwrite=False, source=None, unmatched='ignore', "
            "vendor='vendor', verbose=False)",
        )

    @patch("sys.stderr", new=StringIO())
    def test_parser_unmatched(self):
        """
        Test handling `unmatched` argument.
        """
        cmd = "-M model -V vendor -u ignore".split(" ")
        args = self.parser.parse_args(cmd)
        self.assertIn("unmatched='ignore'", str(args))

        cmd = "-M model -V vendor -u remove".split(" ")
        args = self.parser.parse_args(cmd)
        self.assertIn("unmatched='remove'", str(args))

        cmd = "-M model -V vendor -u synchronize".split(" ")
        args = self.parser.parse_args(cmd)
        self.assertIn("unmatched='synchronize'", str(args))

        with self.assertRaises(SystemExit):
            cmd = "-M model -V vendor -u foo".split(" ")
            args = self.parser.parse_args(cmd)

    def test_parser_ignored(self):
        """
        Test handling `ignore-file-type` argument.
        """
        cmd = "-M model -V vendor -i txt html".split(" ")
        args = self.parser.parse_args(cmd)
        self.assertIn("ignore_file_type=['txt', 'html']", str(args))

    def test_sync_info_missing(self):
        """
        Test mising sync info raises `ArgumentError`.
        """
        cmd = "-M model -V vendor".split(" ")
        args = self.parser.parse_args(cmd)

        with self.assertRaises(ArgumentError) as exc:
            cli.parse_sync_info(args)

        self.assertEqual(
            str(exc.exception),
            "Either sync mapping file (-f) or source (-s) and destination "
            "(-d) must be defined.",
        )

    def test_sync_info_args(self):
        """
        Test sync info is taken from -s and -d args.
        """
        cmd = "-M model -V vendor -s /src -d /dst".split(" ")
        args = self.parser.parse_args(cmd)

        sources, destinations = cli.parse_sync_info(args)

        self.assertEqual(sources, ["/src"])
        self.assertEqual(destinations, ["/dst"])

    def test_sync_info_file(self):
        """
        Test sync info is taken from mapping file.
        """
        mapping_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "src2dest_example.txt"
        )

        cmd = "-M model -V vendor -f {}".format(mapping_file).split(" ")
        args = self.parser.parse_args(cmd)

        sources, destinations = cli.parse_sync_info(args)

        self.assertEqual(
            sources,
            ["/home/dm/Music/Rock", "/home/dm/Music/discographies/Band1"],
        )
        self.assertEqual(
            destinations, ["Card/Music/Compilations/Rock", "Card/Music/Band1"]
        )

    def test_sync_info_file_incorrect_format(self):
        """
        Test incorrect mapping file format is reported.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            mapping_file = os.path.join(tmp_dir, "incorrect.txt")
            with open(mapping_file, "w") as f:
                f.write("""\n/no/destination/set""")

            cmd = "-M model -V vendor -f {}".format(mapping_file).split(" ")
            args = self.parser.parse_args(cmd)

            with self.assertRaises(MappingFileException) as exc:
                cli.parse_sync_info(args)

            self.assertEqual(
                str(exc.exception),
                'Please separate source and destinationwith "==>".\n'
                'Problematic line: "/no/destination/set"',
            )

    def test_sync_info_args_and_file_are_exclusive(self):
        """
        Test sync info args -s, -d and -f are mutually exclusive.
        """
        cmd = "-M model -V vendor -s /src -d /dst -f file".split(" ")
        args = self.parser.parse_args(cmd)

        with self.assertRaises(ArgumentError) as exc:
            cli.parse_sync_info(args)

        self.assertEqual(
            str(exc.exception),
            "Source (-s) and destination (-d) cannot be set when syncing "
            "from file (-f).",
        )

    @patch("pysyncdroid.find_device.lsusb")
    def test_main_device_exception(self, mock_lsusb):
        """
        Test `DeviceException` exception is handled.
        """
        mock_lsusb.return_value = ""

        cmd = "-M model -V vendor -s /src -d /dst".split(" ")
        args = self.parser.parse_args(cmd)

        self.assertEqual(
            cli.main(args),
            'Device "vendor model" not found.\nNo "vendor" devices were found.',  # noqa
        )

    @patch("pysyncdroid.cli.get_connection_details")
    def test_main_sync_info_exception(self, mock_get_connection_details):
        """
        Test exceptions raised by `parse_sync_info` is handled.
        """
        mock_get_connection_details.return_value = ("usb_bus_id", "device_id")

        cmd = "-M model -V vendor -s /src -d /dst -f file".split(" ")
        args = self.parser.parse_args(cmd)

        self.assertEqual(
            cli.main(args),
            "Source (-s) and destination (-d) cannot be set when syncing "
            "from file (-f).",
        )

    @patch("pysyncdroid.sync.Sync.set_source_abs")
    @patch("pysyncdroid.sync.Sync.set_destination_abs")
    @patch("pysyncdroid.sync.Sync.sync")
    @patch("pysyncdroid.sync.Sync.__init__")
    @patch("pysyncdroid.cli.get_connection_details")
    @patch("pysyncdroid.cli.parse_sync_info")
    def test_main(
        self,
        mock_parse_sync_info,
        mock_get_connection_details,
        mock_sync_init,
        mock_sync_sync,
        mock_set_destination_abs,
        mock_set_source_abs,
    ):
        """
        Test args are parsed and handed over to `Sync`.
        """
        mock_get_connection_details.return_value = ("usb_bus_id", "device_id")
        mock_parse_sync_info.return_value = (["/src"], ["/dst"])
        mock_sync_init.return_value = None

        cmd = "-M model -V vendor -s /src -d /dst -ov".split(" ")
        args = self.parser.parse_args(cmd)
        cli.main(args)

        mock_sync_init.assert_called_once_with(
            destination="/dst",
            ignore_file_types=None,
            mtp_details=(
                "mtp://[usb:usb_bus_id,device_id]/",
                "/run/user/{}/gvfs/mtp:host=%5Busb%3Ausb_bus_id%2C"
                "device_id%5D".format(pwd.getpwnam(getpass.getuser()).pw_uid),
            ),
            overwrite_existing=True,
            source="/src",
            unmatched="ignore",
            verbose=True,
        )
        mock_set_source_abs.assert_called_once_with()
        mock_set_destination_abs.assert_called_once_with()
        mock_sync_sync.assert_called_once_with()

    @patch("pysyncdroid.cli.create_parser")
    @patch("pysyncdroid.cli.main")
    def test_run(self, mock_main, mock_create_parser):
        """
        Test running `cli` module as script.
        """
        mock_create_parser.return_value = self.parser

        cmd = "-M model -V vendor -s /src -d /dst".split(" ")
        args = self.parser.parse_args(cmd)

        with patch("pysyncdroid.cli.__name__", "__main__"):
            # Credits: https://stackoverflow.com/a/8660290/4183498.
            sys.argv[1:] = cmd
            cli.run()

        mock_main.assert_called_once_with(args)
