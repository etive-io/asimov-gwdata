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
            raise(FileNotFoundError)


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
            "phase-1s": "V1:Hrec_hoftRepro1AR_U01_phase_minus1sigma"
            }

        data = {}
            
        for quantity, channel in channel_map.items():
            data[quantity] = TimeSeries.read(frame, channel)

        envelope = np.vstack([
            data['amplitude'].times.value,
            data['amplitude'].data,
            data['phase'].data,
            data['amplitude-1s'].data,
            data['phase-1s'].data,
            data['amplitude+1s'].data,
            data['phase+1s'].data 
        ])

        return envelope

    def frequency_domain_envelope(self, frame, window=np.hamming):
        td_data = self._frame_to_envelopes(frame)

        td_data[0,:] -= td_data[0,0]

        df = td_data[0,1] - td_data[0,0]
        N = len(td_data[0,:])
        frequencies = np.fft.rfftfreq(N, df)
        fd_data = np.zeros((len(frequencies), td_data.shape[0])).T
        fd_data[0,:] = frequencies
        for i, parameter in enumerate(td_data[1:,:]):
            fd_data[i+1,:] = np.fft.rfft(window(N)*parameter)

        return fd_data

    def to_file(self, filename, frequency_domain=True):
        """
        Write the envelope to an ascii file in the format expected by e.g. bilby.

        Parameters
        ----------
        filename: str
          The location the file should be written to.
        frequency_domain: bool
          If True the frequency-domain representation of the envelope is written.
        """

        if frequency_domain:
            envelope = self.data
        else:
            raise NotImplementedError("Time domain envelopes have not yet been implemented in asimov-gwdata.")
        
        np.savetxt(filename, envelope.T, comments="\t".join(["Frequency", "Median mag", "Median phase (Rad)", "16th percentile mag", "16th percentile phase",  "84th percentile mag",   "84th percentile phase"]))
        
    def plot(self, filename):
        """
        Plot the calibration envelope.
        """

        f, ax = plt.subplots(2,1, dpi=300, figsize=(4, np.sqrt(4)))

        ax[0].plot(self.data[0,:], self.data[1,:])
        ax[0].fill_between(self.data[0,:], 100*self.data[3,:], 100*self.data[5,:],
                           alpha=0.5)
        ax[0].set_ylim([-7, 7])
        
        ax[1].plot(self.data[0,:], self.data[2,:])
        ax[1].fill_between(self.data[0,:], self.data[4,:]*1e3, self.data[6,:]*1e3, alpha=0.5)

        ax[1].set_ylim([-4, 4])

        f.savefig(filename)
