"""
Code to work with calibration files.
"""

from gwpy.frequencyseries import FrequencySeries
from gwpy.timeseries import TimeSeries
import numpy as np
import matplotlib.pyplot as plt


class CalibrationUncertaintyEnvelope:
    """
    A class to represent an uncertainty envelope.
    """

    def __init__(self, frame=None):

        if frame:
            self.data = self.frequency_domain_envelope(frame)

        else:
            raise (FileNotFoundError)

    def _frame_to_envelopes(self, frame):
        """
        Read the representation of the calibration uncertainty envelope.
        """

        channel_map = {
            "amplitude": "V1:Hrec_hoftRepro1AR_U01_mag_bias",
            "amplitude-1s": "V1:Hrec_hoftRepro1AR_U01_mag_minus1sigma",
            "amplitude+1s": "V1:Hrec_hoftRepro1AR_U01_mag_plus1sigma",
            "phase": "V1:Hrec_hoftRepro1AR_U01_phase_bias",
            "phase+1s": "V1:Hrec_hoftRepro1AR_U01_phase_plus1sigma",
            "phase-1s": "V1:Hrec_hoftRepro1AR_U01_phase_minus1sigma",
        }

        data = {}

        for quantity, channel in channel_map.items():
            data[quantity] = TimeSeries.read(frame, channel)

        envelope = np.vstack(
            [
                data["amplitude"].times.value,
                data["amplitude"].data,
                data["phase"].data,
                data["amplitude-1s"].data,
                data["phase-1s"].data,
                data["amplitude+1s"].data,
                data["phase+1s"].data,
            ]
        )

        return envelope

    def frequency_domain_envelope(self, frame, window=np.hamming, srate=16000):
        """
        Compute the frequency-domain representation of the envelope.

        Parameters
        ----------
        frame : str
          The filepath of the frame file.
        window : func
          A function to use to envelope the data.
        srate : int
          The sampling rate of the data, defaults to 16000kHz, which is the Virgo default.

        """
        td_data = self._frame_to_envelopes(frame)
        td_data[0, :] = np.linspace(0, srate, td_data.shape[1])
        return td_data

    def to_file(self, filename):
        """
        Write the envelope to an ascii file in the format expected by e.g. bilby.

        Parameters
        ----------
        filename: str
          The location the file should be written to.
        """
        envelope = self.data
        np.savetxt(
            filename,
            envelope.T,
            comments="\t".join(
                [
                    "Frequency",
                    "Median mag",
                    "Median phase (Rad)",
                    "16th percentile mag",
                    "16th percentile phase",
                    "84th percentile mag",
                    "84th percentile phase",
                ]
            ),
        )

    def plot(self, filename, save=True):
        """
        Plot the calibration envelope.
        """

        f, ax = plt.subplots(2, 1, dpi=300, figsize=(4*np.sqrt(2), 4),
                             sharey=True,
                             layout="constrained")

        xaxis = self.data[0, :]

        ax[0].plot(xaxis, self.data[1, :])
        ax[0].fill_between(xaxis, self.data[3, :], self.data[5, :], alpha=0.5)
        ax[0].set_title("magnitude")
        ax[0].set_xlabel("Frequency / Hz")
        ax[1].plot(xaxis, self.data[2, :])
        ax[1].fill_between(xaxis, self.data[4, :], self.data[6, :], alpha=0.5)
        ax[1].set_title("phase")
        ax[1].set_xlabel("Frequency / Hz")
        if save:
            f.savefig(filename)

        return f
