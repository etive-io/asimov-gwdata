import requests
import shutil
import os
import glob

import yaml

import numpy as np

from gwosc.locate import get_urls
from pesummary.io import read
from asimov.utils import set_directory
import click

import logging

logger = logging.getLogger("gwdata")

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


def get_o4_style_calibration(dir, time):
    data = {}
    for ifo in ["H1", "L1"]:
        file_list = glob.glob(
            os.path.join(
                f"{dir}",
                f"{ifo}",
                "uncertainty",
                "*",
                "*",
                f"calibration_uncertainty_{ifo}_*.txt",
            )
        )
        files_by_time = {int(datum[-14:-4]): datum for datum in file_list}
        times = np.array(list(files_by_time.keys())) - time
        data_file = list(files_by_time.items())[np.argmin(np.abs(times))]
        data[ifo] = data_file[1]
    return data


def find_calibrations(time):
    """
    Find the calibration file for a given time.
    """

    observing_runs = {
        "O1":  [1126623617, 1136649617],
        "O2":  [1164556817, 1187733618],
        "O3a": [1238166018, 1253977218],
        "O3b": [1256655618, 1269363618],
        "O4a": [1368975618, 1384873218],
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
        dir = os.path.join(os.path.sep, "home", "cal", "public_html", "uncertainty", "O2C02")
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
        dir = os.path.join(os.path.sep, "home", "cal", "public_html", "uncertainty", "O3C01")
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
        dir = os.path.join(os.path.sep, "home", "cal", "public_html", "archive")
        data = get_o4_style_calibration(dir, time)
        logger.debug(f"Found envelopes: {data}")

    elif not run:
        # This time is outwith a valid observing run
        data = {}

    for ifo, envelope in data.items():
        copy_file(envelope, rename=f"{ifo}.txt", directory="calibration")

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
        find_calibrations(settings["time"]["start"])
        settings["data"].remove("calibration")

    if "posterior" in settings["data"]:
        get_pesummary(components=settings["data"], settings=settings)
        settings["data"].remove("posterior")


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

        if component == "psds":
            os.makedirs("psds", exist_ok=True)
            analysis_data = data.psd[analysis]
            for ifo, psd in analysis_data.items():
                with set_directory("psds"):
                    psd.save_to_file(f"{ifo}.dat", delimiter="\t")


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

    click.echo("Frames found")
    click.echo("------------")
    for det, url in files.items():
        click.echo(click.style(f"{det}: ", bold=True), nl=False)
        click.echo(url[0])
    return urls
