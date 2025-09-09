"""
Code to work with calibration files.
"""
import logging
import os
import glob
import re

from gwpy.timeseries import TimeSeriesDict

import lal, lalframe

import numpy as np
import matplotlib.pyplot as plt

from .frames import Frame, get_data_frames_private

logger = logging.getLogger("gwdata")

class CalibrationUncertaintyEnvelope:
    """
    A class to represent an uncertainty envelope.
    """

    def __init__(self):
        pass

    @classmethod
    def from_array(cls, data, *args, **kwargs):
        """
        Create an envelope from a data array.
        """
        instance = cls(*args, **kwargs)
        instance.data = np.array(data).T

        return instance

    @classmethod
    def from_file(cls, filename, *args, **kwargs):
        """
        Turn an ascii file into a CalibrationUncertaintyEnvelope
        """
        instance = cls(*args, **kwargs)
        instance.data = np.genfromtxt(filename)

        return instance

    @classmethod
    def from_frame(cls, frame, *args, **kwargs):
        """
        Create an envelope by extracting it from a frame file.
        """
        instance = cls(*args, **kwargs)
        instance.data = instance.frequency_domain_envelope(frame=frame)

        return instance

    def _frame_to_envelopes(self, frame, calibration="U00"):
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
        channel = f"V1:Hrec_hoft_{calibration}_lastWriteGPS"
        frfile = lalframe.FrOpen(os.path.dirname(frame), os.path.basename(frame))
        epoch = frfile.epoch
        #lalframe.FrClose(frfile)
        time = Frame(frame).nearest_calibration(time=epoch, channel=channel)
        time=epoch
        stream = lalframe.FrStreamOpen(os.path.dirname(frame), os.path.basename(frame))
        print(dir(stream))
        for name, channel in channel_map.items():

            #frdatatype = lalframe.FrStreamGetFrequencySeriesType(channel, stream)
            data[channel] = lalframe.FrStreamReadREAL8FrequencySeries(stream, channel, time)
            f0 = data[channel].f0
            delta_f = data[channel].deltaF
            n_bins = data[channel].data.length
            frequencies = np.linspace(f0, f0 + delta_f * (n_bins - 1), n_bins)
            # Only include frequencies greater than 10Hz
            mask = frequencies >= 10.0
        #lalframe.FrClose(stream)
        amp = data[channel_map["amplitude"]].data.data[mask]
        phase = data[channel_map["phase"]].data.data[mask]
        envelope = np.vstack(
            [
                frequencies[mask],
                amp
                phase,
                amp + data[channel_map["amplitude-1s"]].data.data[mask],
                phase + data[channel_map["phase-1s"]].data.data[mask],
                amp + data[channel_map["amplitude+1s"]].data.data[mask],
                phase + data[channel_map["phase+1s"]].data.data[mask],
            ]
        )

        return envelope

    def frequency_domain_envelope(self, frame=None, time=None, srate=16000):
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
        if frame:
            td_data = self._frame_to_envelopes(frame)
        elif time:
            td_data = self._nds_to_envelopes(time)
        else:
            logger.error("No source specified for the calibration data.")
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

def get_calibration_from_frame(
    ifo,
    time,
    host="datafind.igwn.org",
    calibration="U00",
    frametype="V1:HoftAR1"):
    """
    Retrieve a calibration file from a frame file.

    Parameters
    ----------
    ifo : str
      The interferometer to get the calibration data for.
    time: int
      The gpstime which calibration is required for.
    host : str, optional
      The URL of the datafind server which should be queried to retrieve frame file information.
      Defaults to datafind.igwn.org
    frametype : str, optional
      The frametype to be used to retrieve calibration uncertainty data from.
    """
    start = time - 60
    end = time + 60
    frame = get_data_frames_private([frametype], start, end, download=True, host=host)[1][0]
    channel = f"V1:Hrec_hoft_{calibration}_lastWriteGPS"
    if not (nearest := Frame(frame).nearest_calibration(channel)) in frame:
        frame = get_data_frames_private([frametype], nearest-1, nearest+1, download=True, host=host)[1][0]

    envelope = CalibrationUncertaintyEnvelope.from_frame(frame=frame)
    envelope.to_file(os.path.join("calibration", f"{ifo}.dat"))


def get_o3_style_calibration(dir, time):
    data_llo = glob.glob(os.path.join(f"{dir}", "L1", "*LLO*FinalResults.txt"))
    times_llo = {
        int(datum.split("GPSTime_")[1].split("_C0")[0]): datum for datum in data_llo
    }

    data_lho = glob.glob(os.path.join(f"{dir}", "H1", "*LHO*FinalResults.txt"))
    times_lho = {
        int(datum.split("GPSTime_")[1].split("_C0")[0]): datum for datum in data_lho
    }

    keys_llo = np.array(list(times_llo.keys()))
    keys_lho = np.array(list(times_lho.keys()))

    return {
        "H1": times_lho[keys_lho[np.argmin(np.abs(keys_lho - time))]],
        "L1": times_llo[keys_llo[np.argmin(np.abs(keys_llo - time))]],
    }


def get_o4_style_calibration(dir, time, version="v1"):
    data = {}
    for ifo in ["H1", "L1"]:
        if isinstance(version, dict):
            ifo_version = version.get(ifo)
        else:
            ifo_version = version
        file_list_globbed = glob.glob(
            os.path.join(
                f"{dir}",
                f"{ifo}",
                "uncertainty",
                f"{ifo_version}",
                "*",
                "*",
                f"calibration_uncertainty_{ifo}_*[0-9].txt",
            )
        )
        regex_string = fr".*\/calibration_uncertainty_{ifo}_([0-9]{{1,}}).txt"
        regex = re.compile(regex_string)
        files_by_time = {}
        for calib_file in file_list_globbed:
            m = regex.match(calib_file)
            if m:
                files_by_time[int(m.group(1))] = calib_file
        if len(files_by_time) > 0:
            times = np.array(list(files_by_time.keys())) - time
            data_file = list(files_by_time.items())[np.argmin(np.abs(times))]
            data[ifo] = data_file[1]
    return data


def find_calibrations(time, base_dir=None, version=None):
    """
    Find the calibration file for a given time.

    Parameters
    ----------
    time : number
       The GPS time for which the nearest calibration should be returned.
    base_dir: str
       The base directory to search for calibration envelopes.
       By default will use the default location.
    """

    observing_runs = {
        "O1":   [1126623617, 1136649617],
        "O2":   [1164556817, 1187733618],
        "O3a":  [1238166018, 1253977218],
        "O3b":  [1256655618, 1269363618],
        "ER15": [1366556418, 1368975618], #  2023-04-26 15:00 to 2023-05-24 15:00
        "O4a":  [1368975618, 1389456018], #  2023-05-24 15:00 to 2024-01-16 16:00
        "ER16": [1394982018, 1396792818], #  2024-03-20 15:00 to 2024-04-10 14:00
        "O4b":  [1396792818, 1422118818], #  2024-04-10 14:00 to 2025-01-28 17:00
        "O4c":  [1422118818, 1443884418], #  2025-01-28 17:00 to 2025-10-07 15:00
    }

    def identify_run_from_gpstime(time):
        for run, (start, end) in observing_runs.items():
            if start < time < end:
                return run
        return None

    run = identify_run_from_gpstime(time)

    if run == "O1":
        logger.error("Cannot retrieve calibration undertainty envelopes for O1 events")

    if run == "O2":
        # This looks like an O2 time
        logger.info("Retrieving O2 calibration envelopes")
        dir = os.path.join(
            os.path.sep, "home", "cal", "public_html", "uncertainty", "O2C02"
        )
        virgo = os.path.join(
            os.path.sep,
            "home",
            "carl-johan.haster",
            "projects",
            "O2",
            "C02_reruns",
            "V_calibrationUncertaintyEnvelope_magnitude5p1percent_phase40mraddeg20microsecond.txt",
        )  # NoQA
        data = get_o3_style_calibration(dir, time)
        data["V1"] = virgo
        logger.debug(f"Found envelopes: {data}")

    elif run in ("O3a", "O3b"):
        # This looks like an O3 time
        logger.info("Retrieving O3 calibration envelopes")
        dir = os.path.join(
            os.path.sep, "home", "cal", "public_html", "uncertainty", "O3C01"
        )
        virgo = os.path.join(
            os.path.sep,
            "home",
            "cbc",
            "pe",
            "O3",
            "calibrationenvelopes",
            "Virgo",
            "V_O3a_calibrationUncertaintyEnvelope_magnitude5percent_phase35milliradians10microseconds.txt",
        )  # NoQA
        data = get_o3_style_calibration(dir, time)
        data["V1"] = virgo
        logger.debug(f"Found envelopes: {data}")

    elif run in ("O4a", "O4b", "O4c"):
        # This looks like an O4 time
        logger.info("Retrieving O4 calibration envelopes")
        if base_dir:
            dir = base_dir
        else:
            dir = os.path.join(os.path.sep, "home", "cal", "public_html", "archive")
        data = get_o4_style_calibration(dir, time, version)

        logger.info("Virgo calibration has been requested but this must be retrieved from a frame file.")
        data["V1"] = calibration.get_calibration_from_frame("V1", time)

        logger.debug(f"Found envelopes: {data}")

    elif not run:
        # This time is outwith a valid observing run
        data = {}

    for ifo, envelope in data.items():
        copy_file(envelope, rename=f"{ifo}.txt", directory="calibration")

    if len(data) == 0:
        logger.error(f"No calibration uncertainty envelopes found.")
    else:

        click.echo("Calibration uncertainty envelopes found")
        click.echo("---------------------------------------")
        for det, url in data.items():
            click.echo(click.style(f"{det}: ", bold=True), nl=False)
            click.echo(f"{url}")

    return data
