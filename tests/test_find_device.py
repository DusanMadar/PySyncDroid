"""Tests for device finding functionality."""


import unittest
from unittest.mock import patch

from pysyncdroid.exceptions import DeviceException
from pysyncdroid.find_device import (
    get_connection_details,
    get_mtp_details,
    lsusb,
)


mock_lsub_parts = [
    "Bus 002 Device 001: ID 0123:0001 test_vendor test_model1",
    "Bus 002 Device 002: ID 0456:0002 test_vendor test_model2",
    "Bus 002 Device 003: ID 0789:0003 test_vendor test_model3",
    "Bus 002 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub",
    "Bus 004 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub",
]
MOCK_LSUB_RESULT = "\n".join(mock_lsub_parts)


class TestLsusb(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("pysyncdroid.find_device.run_bash_cmd")
        self.mock_run_bash_cmd = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_lsusb(self):
        lsusb()

        self.mock_run_bash_cmd.assert_called_with(["lsusb"])


class TestFindDevice(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("pysyncdroid.find_device.lsusb")
        self.mock_lsusb = self.patcher.start()
        self.mock_lsusb.return_value = MOCK_LSUB_RESULT

    def tearDown(self):
        self.patcher.stop()

    def test_get_connection_details_device_exception(self):
        """
        Test 'get_connection_details' raises a DeviceException with an
        appropriate error message when trying to find a non-existent device.
        """
        with self.assertRaises(DeviceException) as exc:
            get_connection_details(
                vendor="non-existent-vendor", model="non-existent-model"
            )

        exc_msg_parts = (
            'Device "non-existent-vendor non-existent-model" not found.',
            'No "non-existent-vendor" devices were found.',
        )

        self.assertEqual(str(exc.exception), "\n".join(exc_msg_parts))

    def test_get_connection_details_device_exception_message(self):
        """
        Test 'get_connection_details' raises a DeviceException and the provided
        error message lists all vendor devices when trying to find a
        non-existent model.
        """
        with self.assertRaises(DeviceException) as exc:
            get_connection_details(vendor="linux", model="non-existent-model")

        exc_msg_parts = (
            'Device "linux non-existent-model" not found.',
            'Following "linux" devices were found:',
            "Linux Foundation 2.0 root hub",
            "Linux Foundation 3.0 root hub",
        )

        self.assertEqual(str(exc.exception), "\n".join(exc_msg_parts))

    def test_get_connection_details_multiple_devices(self):
        """
        Test 'get_connection_details' is able to find the given device in case
        of multiple devices from the same vendor (i.e. it doesn't pick up the
        first device for a certain vendor).
        """
        connection_details = get_connection_details(
            vendor="test_vendor", model="test_model3"
        )

        self.assertIsInstance(connection_details, tuple)
        self.assertEqual(connection_details[0], "002")
        self.assertEqual(connection_details[1], "003")

    def test_get_mtp_details(self):
        """
        Test 'get_mtp_details' returns a valid MTP url gvfs path.
        """
        usb_bus, device = get_connection_details(vendor="linux", model="root")

        mtp_details = get_mtp_details(usb_bus, device)
        self.assertIsInstance(mtp_details, tuple)

        for mtp_detail in mtp_details:
            self.assertIn(device, mtp_detail)
            self.assertIn(usb_bus, mtp_detail)
