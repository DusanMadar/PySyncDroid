"""Tests for gvfs wrappers."""


import unittest
from unittest.mock import call, patch

from pysyncdroid.gvfs import cp, mkdir, mv, mount, rm


class TestGvfsWrappers(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("pysyncdroid.gvfs.run_bash_cmd")
        self.mock_run_bash_cmd = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_cp(self):
        src = "/src"
        dst = "/dst"
        cp(src, dst)

        self.mock_run_bash_cmd.assert_called_with(["gvfs-copy", src, dst])

    def test_mkdir(self):
        path = "/dst/path"
        mkdir(path)

        self.mock_run_bash_cmd.assert_called_with(["gvfs-mkdir", "-p", path])

    def test_mount(self):
        mtp_url = "mtp://[usb:2,3]/"
        mount(mtp_url)

        self.mock_run_bash_cmd.assert_called_with(["gvfs-mount", mtp_url])

    def test_mv(self):
        src = "/src"
        dst = "/dst"
        mv(src, dst)

        self.assertEqual(self.mock_run_bash_cmd.call_count, 2)
        # order is important here
        calls = (
            call(["gvfs-copy", src, dst]),
            call(["gvfs-rm", "-f", "/src"]),
        )
        self.mock_run_bash_cmd.assert_has_calls(calls)

    def test_rm(self):
        src = "/src"
        rm(src)

        self.mock_run_bash_cmd.assert_called_with(["gvfs-rm", "-f", src])
