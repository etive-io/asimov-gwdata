"""
Code to work with calibration files.
"""

from gwpy.frequencyseries import FrequencySeries
from gwpy.timeseries import TimeSeries
import numpy as np

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

    def frequency_domain_envelope(self, frame):
        td_data = self._frame_to_envelopes(frame)

        td_data[0,:] -= td_data[0,0]

        df = td_data[0,1] - td_data[0,0]
        N = len(td_data[0,:])
        frequencies = np.fft.rfftfreq(N, df)
        fd_data = np.zeros((len(frequencies), td_data.shape[0])).T
        fd_data[0,:] = frequencies
        for i, parameter in enumerate(td_data[1:,:]):
            fd_data[i,:] = np.fft.rfft(parameter)

        return fd_data
