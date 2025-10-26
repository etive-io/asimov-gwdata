"""
Test the various data-download utilities.
"""

import unittest
import datafind.utils as utils

class TestDataDownloadUtils(unittest.TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_download_from_zenodo(self):
        record_id = 14279382
        directory = "roq"
        download_files = ["basis_128s.hdf5"]
        downloaded_files = utils.download_from_zenodo(record_id, directory, download_files)
        assert downloaded_files