import requests
import shutil
import os
import glob
import re

import yaml
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from gwosc.locate import get_urls
from pesummary.io import read
import click

import logging

from .metafiles import Metafile


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


def copy_file(path, rename, directory):
    os.makedirs(directory, exist_ok=True)
    local_filename = rename
    shutil.copyfile(path, os.path.join(directory, local_filename))
    return local_filename


def download_file(url, directory="frames"):
    os.makedirs(directory, exist_ok=True)
    local_filename = url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        with open(os.path.join(directory, local_filename), "wb") as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename


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

    elif run in ("O4a", "O4b"):
        # This looks like an O4 time
        logger.info("Retrieving O4 calibration envelopes")
        if base_dir:
            dir = base_dir
        else:
            dir = os.path.join(os.path.sep, "home", "cal", "public_html", "archive")
        data = get_o4_style_calibration(dir, time, version)
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


@click.command()
@click.option("--settings")
def get_data(settings):  # detectors, start, end, duration, frames):
    with open(settings, "r") as file_handle:
        settings = yaml.safe_load(file_handle)

    if "frames" in settings["data"]:
        get_data_frames(
            settings["interferometers"],
            settings["time"]["start"],
            settings["time"]["end"],
            settings["time"]["duration"],
        )
        settings["data"].remove("frames")

    if "calibration" in settings["data"]:
        directory = settings.get("locations", {}).get("calibration directory", None)
        find_calibrations(
            settings["time"]["start"],
            directory,
            version=settings.get("calibration version", "v1"),
        )
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

        if component == "calibration":
            calibration_data = data.priors["calibration"][analysis]
            os.makedirs("calibration", exist_ok=True)
            for ifo, calibration in calibration_data.items():
                with set_directory("calibration"):
                    calibration.save_to_file(f"{ifo}.dat", delimiter="\t")

        if component == "posterior":
            os.makedirs("posterior", exist_ok=True)
            shutil.copy(location, os.path.join("posterior", "metafile.h5"))
            # analysis_data = data.samples_dict[analysis]
            # analysis_data.write(package="gw", file_format="dat", filename="posterior/posterior_samples.dat")

def get_data_frames(detectors, start, end, duration):
    urls = {}
    files = {}
    for detector in detectors:
        det_urls = get_urls(
            detector=detector, start=start, end=end, sample_rate=16384, format="gwf"
        )
        det_urls_dur = []
        det_files = []
        for url in det_urls:
            duration_u = int(url.split("/")[-1].split(".")[0].split("-")[-1])
            filename = url.split("/")[-1]
            if duration_u == duration:
                det_urls_dur.append(url)
                download_file(url)
                det_files.append(filename)
        urls[detector] = det_urls_dur
        files[detector] = det_files

    os.makedirs("cache", exist_ok=True)
    for detector in detectors:
        cache_string = ""
        for frame_file in files[detector]:
            cf = frame_file.split(".")[0].split("-")
            frame_file = os.path.join("frames", frame_file)
            cache_string += f"{cf[0]}\t{cf[1]}\t{cf[2]}\t{cf[3]}\tfile://localhost{os.path.abspath(frame_file)}\n"
        with open(os.path.join("cache", f"{detector}.cache"), "w") as cache_file:
            cache_file.write(cache_string)

    click.echo("Frames found")
    click.echo("------------")
    for det, url in files.items():
        click.echo(click.style(f"{det}: ", bold=True), nl=False)
        click.echo(url[0])
    return urls


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
