"""
Tests for ``datafind.plotting.plot_spectrogram`` and ``Frame.spectrogram``.

Real Q-transform signal processing (``gwpy.timeseries.TimeSeries``) is
mocked - these tests only check the dispatch/plumbing, not the actual
plot output.
"""
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from datafind.frames import Frame
from datafind.plotting import plot_spectrogram


class TestPlotSpectrogram(unittest.TestCase):
    def test_raises_clear_error_without_time_or_window(self):
        """
        Regression test: calling plot_spectrogram() with none of `time`,
        `start`, or `end` used to crash with a TypeError from doing
        arithmetic on None, rather than a clear, actionable error.
        """
        with self.assertRaises(ValueError):
            plot_spectrogram("H-H1_STRAIN-1-32.gwf", "H1:STRAIN")

    def test_raises_clear_error_with_only_start(self):
        with self.assertRaises(ValueError):
            plot_spectrogram("H-H1_STRAIN-1-32.gwf", "H1:STRAIN", start=100.0)


class TestFrameSpectrogram(unittest.TestCase):
    def test_spectrogram_with_explicit_channel(self):
        with patch("datafind.frames.plot_spectrogram") as mock_plot, patch(
            "datafind.frames.get_channel_names", return_value=["H1:STRAIN"]
        ):
            fake_figure = MagicMock()
            mock_plot.return_value = fake_figure

            frame = Frame("H-H1_STRAIN-1-32.gwf")
            result = frame.spectrogram(channel="H1:STRAIN", time=1126259462)

            mock_plot.assert_called_once_with(
                "H-H1_STRAIN-1-32.gwf", "H1:STRAIN", time=1126259462
            )
            self.assertIs(result, fake_figure)

    def test_spectrogram_defaults_to_midpoint_time_when_not_given(self):
        with patch("datafind.frames.plot_spectrogram") as mock_plot, patch(
            "datafind.frames.get_channel_names", return_value=["H1:STRAIN"]
        ), patch("datafind.frames.TimeSeries") as mock_ts_cls:
            fake_data = MagicMock()
            fake_data.times.value = np.array([100.0, 101.0, 102.0])
            fake_data.__len__.return_value = 3
            mock_ts_cls.read.return_value = fake_data

            frame = Frame("H-H1_STRAIN-1-32.gwf")
            frame.spectrogram(channel="H1:STRAIN")

            mock_plot.assert_called_once_with(
                "H-H1_STRAIN-1-32.gwf", "H1:STRAIN", time=101.0
            )

    def test_spectrogram_tries_every_channel_when_none_given(self):
        with patch("datafind.frames.plot_spectrogram") as mock_plot, patch(
            "datafind.frames.get_channel_names", return_value=["H1:STRAIN", "H1:AUX"]
        ):
            fake_figure = MagicMock()
            mock_plot.side_effect = [RuntimeError("bad channel"), fake_figure]

            frame = Frame("H-H1_STRAIN-1-32.gwf")
            result = frame.spectrogram(time=1126259462)

            self.assertEqual(mock_plot.call_count, 2)
            self.assertIs(result, fake_figure)

    def test_spectrogram_stops_after_first_success(self):
        """
        Regression test: spectrogram() used to keep trying every remaining
        channel even after a successful plot, wasting an expensive
        Q-transform per channel and potentially overwriting the first
        successful result with a later, unrelated one.
        """
        with patch("datafind.frames.plot_spectrogram") as mock_plot, patch(
            "datafind.frames.get_channel_names",
            return_value=["H1:STRAIN", "H1:AUX"],
        ):
            fake_figure = MagicMock()
            mock_plot.return_value = fake_figure

            frame = Frame("H-H1_STRAIN-1-32.gwf")
            result = frame.spectrogram(time=1126259462)

            mock_plot.assert_called_once()
            self.assertIs(result, fake_figure)

    def test_spectrogram_returns_none_when_every_channel_fails(self):
        with patch("datafind.frames.plot_spectrogram") as mock_plot, patch(
            "datafind.frames.get_channel_names", return_value=["H1:STRAIN"]
        ):
            mock_plot.side_effect = RuntimeError("bad channel")

            frame = Frame("H-H1_STRAIN-1-32.gwf")
            result = frame.spectrogram(time=1126259462)

            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
