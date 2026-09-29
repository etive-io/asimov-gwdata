"""
Test the various data-download utilities.
"""
import os
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

from datafind.utils import download_from_zenodo
from tests.test_fixtures import temporary_test_directory


ZENODO_RECORD_RESPONSE = {
    "files": [
        {
            "key": "basis_128s.hdf5",
            "links": {"self": "https://zenodo.org/api/records/14279382/files/basis_128s.hdf5/content"},
        },
        {
            "key": "basis_256s.hdf5",
            "links": {"self": "https://zenodo.org/api/records/14279382/files/basis_256s.hdf5/content"},
        },
    ]
}


class TestDataDownloadUtils(unittest.TestCase):
    """
    These tests mock out the Zenodo API and file downloads, so they run
    offline and don't depend on a specific record's contents.
    """

    def _mock_get(self, url, **kwargs):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=False)
        if url == "https://zenodo.org/api/records/14279382":
            response.json.return_value = ZENODO_RECORD_RESPONSE
        else:
            response.raw = BytesIO(b"fake file contents")
        return response

    @patch("datafind.utils.requests.get")
    def test_download_from_zenodo_downloads_all_files_by_default(self, mock_get):
        mock_get.side_effect = self._mock_get
        with temporary_test_directory() as tmpdir:
            downloaded = download_from_zenodo(14279382, directory=os.path.join(tmpdir, "roq"))
            self.assertEqual(len(downloaded), 2)
            for path in downloaded:
                self.assertTrue(os.path.exists(path))

    @patch("datafind.utils.requests.get")
    def test_download_from_zenodo_filters_to_requested_files(self, mock_get):
        mock_get.side_effect = self._mock_get
        with temporary_test_directory() as tmpdir:
            downloaded = download_from_zenodo(
                14279382, directory=os.path.join(tmpdir, "roq"), files=["basis_128s.hdf5"]
            )
            self.assertEqual(len(downloaded), 1)
            self.assertTrue(downloaded[0].endswith("basis_128s.hdf5"))


if __name__ == "__main__":
    unittest.main()
