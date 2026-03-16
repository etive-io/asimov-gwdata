"""
Tests to check that frames can be properly accessed.
"""

import os
import unittest
import datafind.frames
import requests.exceptions

from unittest.mock import MagicMock, Mock, mock_open, patch

import igwn_auth_utils

try:
    a = igwn_auth_utils.find_scitoken(audience="https://datafind.igwn.org", scope="gwdatafind.read")
    logged_in=True
except igwn_auth_utils.IgwnAuthError as e:
    print(e)
    logged_in=False



class TestFrameClass(unittest.TestCase):
    def setUp(self):
        pass

    def test_time_in_frame(self):
        try:
            frame = datafind.frames.Frame("tests/test_data/V-HoftAR1-1423946000-2000.gwf")
            self.assertTrue(1423946000.0 in frame)
        except (FileNotFoundError, ImportError):
            self.skipTest("Cannot access frame file.")

class TestLIGOFrames(unittest.TestCase):
    def setUp(self):
        pass

    @unittest.skip("Skip while ER8 data is missing")
    @unittest.skipIf(logged_in==False, "No scitoken was found")
    def test_lookup_gw150914(self):
        try:
            urls, files = datafind.frames.get_data_frames_private(
                types=["H1:H1_HOFT_C02",
                       "L1:L1_HOFT_C02"],
                start=1126259460,
                end=1126259464,
            )
            self.assertEqual(urls['H1'][0],
                     "file://localhost/cvmfs/oasis.opensciencegrid.org/ligo/frames/ER8/hoft_C02/H1/H-H1_HOFT_C02-11262/H-H1_HOFT_C02-1126256640-4096.gwf")
        except requests.exceptions.HTTPError:
            self.skipTest("Cannot access gw_data_find.")

    @unittest.skip("Skip while ER8 data is missing")
    @unittest.skipIf(logged_in==False, "No scitoken was found")
    @patch('shutil.copyfile')
    def test_download_gw150914(self, mock_shutil):

        mock_shutil.return_value = True

        try:
            urls, files = datafind.frames.get_data_frames_private(
                types=["H1:H1_HOFT_C02",
                       "L1:L1_HOFT_C02"],
                start=1126259460,
                end=1126259464,
                download=True,
            )

            self.assertEqual(files['H1'], ['H-H1_HOFT_C02-1126256640-4096.gwf'])
        except requests.exceptions.HTTPError:
            self.skipTest("Cannot access gw_data_find.")


class TestCacheFileGeneration(unittest.TestCase):
    """Tests to verify GW cache files are correctly formatted."""

    FRAME_FILENAME = "H-H1_HOFT_C02-1126256640-4096.gwf"
    ABS_FRAME_PATH = "/working/dir/frames/H-H1_HOFT_C02-1126256640-4096.gwf"

    def _get_written_cache_line(self, mock_file):
        """Extract the string passed to cache file's write() call."""
        handle = mock_file.return_value.__enter__.return_value
        return handle.write.call_args[0][0]

    @patch("datafind.frames.os.path.abspath", return_value=ABS_FRAME_PATH)
    @patch("datafind.frames.os.makedirs")
    @patch("datafind.frames.download_file", return_value=FRAME_FILENAME)
    @patch("datafind.frames.find_urls", return_value=["osdf://path/to/H-H1_HOFT_C02-1126256640-4096.gwf"])
    @patch("datafind.frames.Session")
    def test_private_frames_cache_format(
        self, mock_session, mock_find_urls, mock_download, mock_makedirs, mock_abspath
    ):
        """Cache files written by get_data_frames_private are correctly formatted."""
        mock_session.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_session.return_value.__exit__ = Mock(return_value=False)

        m = mock_open()
        with patch("builtins.open", m):
            datafind.frames.get_data_frames_private(
                types=["H1:H1_HOFT_C02"],
                start=1126256640,
                end=1126260736,
                download=True,
            )

        written = self._get_written_cache_line(m)
        parts = written.strip().split("\t")

        self.assertEqual(len(parts), 5, f"Cache line should have 5 tab-separated fields, got: {parts}")
        self.assertEqual(parts[0], "H",            "First field should be the IFO prefix")
        self.assertEqual(parts[1], "H1_HOFT_C02",  "Second field should be the frame type")
        self.assertEqual(parts[2], "1126256640",   "Third field should be the GPS start time")
        self.assertEqual(parts[3], "4096",         "Fourth field should be the duration in seconds")
        self.assertTrue(parts[4].startswith("file://localhost"), "Fifth field should start with file://localhost")
        self.assertTrue(parts[4].endswith(".gwf"), "Fifth field should end with .gwf")
        self.assertEqual(parts[4], f"file://localhost{self.ABS_FRAME_PATH}")

    @patch("datafind.frames.os.path.abspath", return_value=ABS_FRAME_PATH)
    @patch("datafind.frames.os.makedirs")
    @patch("datafind.frames.download_file")
    @patch("datafind.frames.get_urls")
    def test_gwosc_cache_format(
        self, mock_get_urls, mock_download, mock_makedirs, mock_abspath
    ):
        """Cache files written by get_data_frames_gwosc are correctly formatted."""
        mock_get_urls.return_value = [
            "https://gwosc.org/archive/data/O1/H-H1_HOFT_C02-1126256640-4096.gwf"
        ]

        m = mock_open()
        with patch("builtins.open", m):
            datafind.frames.get_data_frames_gwosc(
                detectors=["H1"],
                start=1126256640,
                end=1126260736,
                duration=4096,
            )

        written = self._get_written_cache_line(m)
        parts = written.strip().split("\t")

        self.assertEqual(len(parts), 5, f"Cache line should have 5 tab-separated fields, got: {parts}")
        self.assertEqual(parts[0], "H",            "First field should be the IFO prefix")
        self.assertEqual(parts[1], "H1_HOFT_C02",  "Second field should be the frame type")
        self.assertEqual(parts[2], "1126256640",   "Third field should be the GPS start time")
        self.assertEqual(parts[3], "4096",         "Fourth field should be the duration in seconds")
        self.assertTrue(parts[4].startswith("file://localhost"), "Fifth field should start with file://localhost")
        self.assertTrue(parts[4].endswith(".gwf"), "Fifth field should end with .gwf")

    @patch("datafind.frames.os.path.abspath", return_value=ABS_FRAME_PATH)
    @patch("datafind.frames.os.makedirs")
    @patch("datafind.frames.download_file")
    @patch("datafind.frames.get_urls")
    def test_gwosc_cache_file_named_by_detector(
        self, mock_get_urls, mock_download, mock_makedirs, mock_abspath
    ):
        """Cache file is named <detector>.cache inside the cache/ directory."""
        mock_get_urls.return_value = [
            "https://gwosc.org/archive/data/O1/H-H1_HOFT_C02-1126256640-4096.gwf"
        ]

        m = mock_open()
        with patch("builtins.open", m) as mock_file:
            datafind.frames.get_data_frames_gwosc(
                detectors=["H1"],
                start=1126256640,
                end=1126260736,
                duration=4096,
            )

        opened_path = mock_file.call_args[0][0]
        self.assertEqual(opened_path, os.path.join("cache", "H1.cache"))
