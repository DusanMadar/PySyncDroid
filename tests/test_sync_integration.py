import os
import tempfile
import unittest

from pysyncdroid.sync import Sync, REMOVE, SYNCHRONIZE
from tests.test_sync import FAKE_MTP_DETAILS


class TestSyncIntegration(unittest.TestCase):
    COPY_FILE = "copy.me"
    DST_FILE = "dst.me"
    DST_DIR = "Directory"

    def test_sync_default(self):
        """
        Test `sync` is able to copy files from src to dst and ignores unmatched
        files from dst.
        """
        with tempfile.TemporaryDirectory() as src_tmp_dir_path:
            with tempfile.TemporaryDirectory() as dst_tmp_dir_path:
                with open(os.path.join(src_tmp_dir_path, self.COPY_FILE), "w"):
                    pass

                sync = Sync(
                    FAKE_MTP_DETAILS,
                    src_tmp_dir_path,
                    os.path.join(dst_tmp_dir_path, self.DST_DIR),
                )
                sync.set_source_abs()
                sync.set_destination_abs()
                sync.sync()

                self.assertTrue(
                    os.path.exists(
                        os.path.join(
                            dst_tmp_dir_path, self.DST_DIR, self.COPY_FILE
                        )
                    )
                )

    def test_sync_removes_unmatched(self):
        """
        Test `sync` is able to copy files from src to dst and removes unmatched
        files from dst.
        """
        with tempfile.TemporaryDirectory() as src_tmp_dir_path:
            with tempfile.TemporaryDirectory() as dst_tmp_dir_path:
                with open(os.path.join(src_tmp_dir_path, self.COPY_FILE), "w"):
                    pass

                dst_dir_path = os.path.join(dst_tmp_dir_path, self.DST_DIR)
                os.makedirs(dst_dir_path)
                with open(os.path.join(dst_dir_path, self.DST_FILE), "w"):
                    pass

                sync = Sync(
                    FAKE_MTP_DETAILS,
                    src_tmp_dir_path,
                    os.path.join(dst_tmp_dir_path, self.DST_DIR),
                    unmatched=REMOVE,
                )
                sync.set_source_abs()
                sync.set_destination_abs()
                sync.sync()

                self.assertTrue(
                    os.path.exists(
                        os.path.join(
                            dst_tmp_dir_path, self.DST_DIR, self.COPY_FILE
                        )
                    )
                )

                self.assertFalse(
                    os.path.exists(os.path.join(dst_dir_path, self.DST_FILE))
                )

    def test_sync_synchronizes_unmatched(self):
        """
        Test `sync` is able to copy files from src to dst and synchornizes
        unmatched files from dst.
        """
        with tempfile.TemporaryDirectory() as src_tmp_dir_path:
            with tempfile.TemporaryDirectory() as dst_tmp_dir_path:
                with open(os.path.join(src_tmp_dir_path, self.COPY_FILE), "w"):
                    pass

                dst_dir_path = os.path.join(dst_tmp_dir_path, self.DST_DIR)
                os.makedirs(dst_dir_path)
                with open(os.path.join(dst_dir_path, self.DST_FILE), "w"):
                    pass

                sync = Sync(
                    FAKE_MTP_DETAILS,
                    src_tmp_dir_path,
                    os.path.join(dst_tmp_dir_path, self.DST_DIR),
                    unmatched=SYNCHRONIZE,
                )
                sync.set_source_abs()
                sync.set_destination_abs()
                sync.sync()

                self.assertTrue(
                    os.path.exists(
                        os.path.join(
                            dst_tmp_dir_path, self.DST_DIR, self.DST_FILE
                        )
                    )
                )

                self.assertTrue(
                    os.path.exists(
                        os.path.join(
                            dst_tmp_dir_path, self.DST_DIR, self.DST_FILE
                        )
                    )
                )

                self.assertTrue(
                    os.path.exists(
                        os.path.join(src_tmp_dir_path, self.DST_FILE)
                    )
                )
