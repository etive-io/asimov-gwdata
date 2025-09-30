"""
Tests to check that frames can be properly accessed.
"""

import unittest
import datafind.frames
import requests.exceptions

from unittest.mock import Mock, patch

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

            self.assertEqual(files['H1'], 'H-H1_HOFT_C02-1126256640-4096.gwf')

        except requests.exceptions.HTTPError:
            self.skipTest("Cannot access gw_data_find.")
