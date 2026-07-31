import requests
import shutil
import os
import glob
import re

import yaml
from contextlib import contextmanager
from pathlib import Path

import numpy as np


from pesummary.io import read
import click

import logging

from .metafiles import Metafile
from . import calibration

from .frames import get_data_frames_gwosc, get_data_frames_private
from .report import Report

logger = logging.getLogger("gwdata")

@contextmanager
def set_directory(path: (Path, str)):
    """
    Change to a different directory for the duration of the context.

    Args:
        path (Path): The path to the cwd

    Yields:
        None
    """

    origin = Path().absolute()
    try:
        logger.info(f"Working temporarily in {path}")
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)
        logger.info(f"Now working in {origin} again")


def download_file(url, directory="frames"):
    os.makedirs(directory, exist_ok=True)
    local_filename = url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        with open(os.path.join(directory, local_filename), "wb") as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename

@click.command()
@click.option("--settings")
def get_data(settings):  # detectors, start, end, duration, frames):
    with open(settings, "r") as file_handle:
        settings = yaml.safe_load(file_handle)

    _report = Report(webdir="report",
                     settings=settings)

    if "frames" in settings["data"]:
        if settings.get("source", {}).get("frames", None) == "osdf":
            get_data_frames_private(
                settings.get("frame types", []),
                settings["time"]["start"],
                settings["time"]["end"],
                download=True,
                host=settings.get("locations", {})\
                    .get("datafind server", "datafind.igwn.org")
            )
        elif (settings.get("source", {}).get("frames", None) == "gwosc") \
            or (settings.get("source", {}).get("frames", None) is None):
            get_data_frames_gwosc(
                settings["interferometers"],
                settings["time"]["start"],
                settings["time"]["end"],
                settings["time"]["duration"],
            )
        else:
            raise ValueError("No source for frames was specified.")
        

        _report.frames = frames
        _report._add_spectrograms()

        settings["data"].remove("frames")

    if "calibration" in settings["data"]:
        source = settings.get("source", {})
        type = source.get("type", None)
        requested_ifos = settings.get("interferometers", [])

        if type == "pesummary":
            # Allow calibration uncertainty envelopes to be extracted from a PESummary metafile.
            summaryfile = settings["source"]["location"]
            analysis = settings["source"].get("analysis", None)
            os.makedirs("calibration", exist_ok=True)
            with Metafile(summaryfile) as metafile:
                for ifo, cal in metafile.calibration(analysis).items():
                    cal.to_file(os.path.join("calibration", f"{ifo}.dat"))

        elif type == "frame":
            # Legacy behaviour: retrieve calibration for a single IFO from a
            # frame file only. This is kept for backwards compatibility with
            # blueprints which use a dedicated analysis just for frame-based
            # (Virgo) calibration. New blueprints do not need to set this
            # explicitly: Virgo calibration is retrieved automatically below,
            # alongside H1/L1, whenever "V1" is listed in `interferometers`.
            for ifo in requested_ifos or ["V1"]:
                # Default to only Virgo since this is the only IFO
                # distributing calibration this way at present.
                if ifo != "V1":
                    logger.error("Only V1 calibration can be retrieved from frame files.")
                    continue

                calibration.get_calibration_from_frame(
                    ifo=ifo,
                    prefix=settings.get("virgo prefix", "V1:Hrec_hoft_U00"),
                    timestamp_channel=settings.get("virgo timestamp channel", None),
                    frametype=settings.get("virgo frametype", "V1:HoftAR1"),
                    time=settings["time"]["start"],
                    host=settings.get("locations", {})\
                    .get("datafind server", "datafind.igwn.org")
                )

        elif (type == "local storage") or (type is None):
            # Default behaviour: fetch calibration for whichever
            # interferometers were requested, in a single pass. H1/L1 (and,
            # for O2/O3 events, V1) come from the local calibration archive
            # -- optionally with a different `calibration version` per
            # interferometer, via a dict. For O4b onwards Virgo calibration
            # isn't distributed as a local text file at all, so if it wasn't
            # found in the archive it is retrieved from a frame file instead,
            # unless local storage was explicitly requested (`source: {type:
            # local storage}`), in which case frame-based retrieval is never
            # attempted. A single analysis listing all the interferometers it
            # needs no longer has to be split across per-IFO/per-source
            # analyses.
            lookup_ifos = list(requested_ifos) if requested_ifos else ["H1", "L1"]

            directory = settings.get("locations", {}).get("calibration directory", None)
            found = calibration.find_calibrations_on_cit(
                settings["time"]["start"],
                directory,
                version=settings.get("calibration version", "v1"),
                interferometers=lookup_ifos,
            )

            if ("V1" in lookup_ifos) and ("V1" not in found) and (type != "local storage"):
                calibration.get_calibration_from_frame(
                    ifo="V1",
                    prefix=settings.get("virgo prefix", "V1:Hrec_hoft_U00"),
                    timestamp_channel=settings.get("virgo timestamp channel", None),
                    frametype=settings.get("virgo frametype", "V1:HoftAR1"),
                    time=settings["time"]["start"],
                    host=settings.get("locations", {})\
                    .get("datafind server", "datafind.igwn.org")
                )
        else:
            logger.error(f"Unrecognised calibration source type: {type}")

        settings["data"].remove("calibration")

    if "posterior" in settings["data"]:
        get_pesummary(components=settings["data"], settings=settings)
        settings["data"].remove("posterior")

    if "psds" in settings["data"]:
        # Gather a PSD from a PESummary Metafile
        if "source" in settings:
            if settings["source"]["type"] == "pesummary":
                summaryfile = settings["source"]["location"]
                analysis = settings["source"].get("analysis", None)
                os.makedirs("psds", exist_ok=True)
                with Metafile(summaryfile) as metafile:
                    for ifo, psd in metafile.psd(analysis).items():
                        psd.to_ascii(os.path.join("psds", f"{ifo}.dat"))
                        psd.to_xml()
            else:
                logger.error("PSDs can only be extracted from PESummary metafiles at present.")
                raise ValueError("The source of PSDs must be a PESummary metafile.")
        else:
            raise ValueError("No metafile location found")

def get_pesummary(components, settings):
    """
    Fetch data from a PESummary metafile.
    """

    # First find the metafile
    if "source" in settings:
        if settings["source"]["type"] == "pesummary":
            location = settings["source"]["location"]
            location = glob.glob(location)[0]
    else:
        raise ValueError("No metafile location found")
    data = read(location, package="gw")
    try:
        analysis = settings["source"]["analysis"]
    except KeyError:
        raise ValueError("No source analysis found in config")

    for component in components:

        if component == "posterior":
            os.makedirs("posterior", exist_ok=True)
            shutil.copy(location, os.path.join("posterior", "metafile.h5"))
            # analysis_data = data.samples_dict[analysis]
            # analysis_data.write(package="gw", file_format="dat", filename="posterior/posterior_samples.dat")

        if component == "psds":
            os.makedirs("psds", exist_ok=True)
            analysis_data = data.psd[analysis]
            for ifo, psd in analysis_data.items():
                with set_directory("psds"):
                    psd.save_to_file(f"{ifo}.dat", delimiter="\t")




def extract_psd_files_from_metafile(metafile, dataset=None):
    """
    Extract the PSD files from the PESummary metafile, and save them
    in txt format as expected by the majority of pipelines.
    """
    output_dictionary = {}
    with h5py.File(metafile) as metafile_handle:
        for ifo in metafile_handle[dataset]["psds"]:
            output_dictionary[ifo] = np.array(metafile_handle[dataset]["psds"][ifo])
    return output_dictionary
