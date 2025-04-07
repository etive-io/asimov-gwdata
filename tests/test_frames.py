"""
Tests to check that frames can be properly accessed.
"""

import unittest
import datafind.frames

class TestLIGOFrames(unittest.TestCase):
    def setUp(self):
        pass

    def test_lookup_gw150914(self):
        urls = datafind.frames.get_data_frames_ligo(
            types=["H1:H1_HOFT_C02",
                   "L1:L1_HOFT_C02"],
            start=1126259460,
            end=1126259464,
        )

    def test_download_gw150914(self):
        urls = datafind.frames.get_data_frames_ligo(
            types=["H1:H1_HOFT_C02",
                   "L1:L1_HOFT_C02"],
            start=1126259460,
            end=1126259464,
            download=True,
        )
