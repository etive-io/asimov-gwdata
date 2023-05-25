import requests
import shutil
import os
import glob

import yaml

import numpy as np

from gwosc.locate import get_urls
from pesummary.io import read, write
from asimov.utils import set_directory
import click


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

    if "frames" in settings["data"]:
        get_data_frames(
            settings["interferometers"],
            settings["time"]["start"],
            settings["time"]["end"],
            settings["time"]["duration"],
        )
        settings["data"].pop("frames")

    get_pesummary(components=settings["data"], settings=settings)
    get_calibration(components=settings["calibration"], settings=settings)


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
        det_urls = get_urls(detector=detector, start=start, end=end, sample_rate=16384, format="gwf")
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


def get_calibration(components, settings):
    """
    Find calibration files.
    """
    # /home/cal/public_html/archive/H1/uncertainty/1364/101222/
    os.makedirs("calibration", exist_ok=True)

    time = settings["event time"]
    ifos = settings["interferometers"]

    if "source" in settings:
        if settings["calibration"]["type"] == "ascii":
            location = settings["calibration"]["location"]
            # e.g. location = /home/cal/public_html/archive/{ifo}/uncertainty/
            files = {}
            for ifo in ifos:
                ifo_location = location.format(ifo=ifo)
                ifo_directories = glob.glob(
                    os.path.join(ifo_location, str(time)[0:4], "*")
                )
                combined = {
                    int(str(time[0:4]))
                    + str(directory): os.path.join(str(time[0:4]), str(directory))
                    for directory in ifo_directories
                }
                keys = list(combined.keys())

                nearest_idx = np.argmin(np.abs(keys - time))
                directory = list(combined.values())[nearest_idx]

                files[ifo] = {
                    "envelope": os.path.join(
                        location,
                        directory,
                        f"calibration_uncertainty_{ifo}_{list(combined.keys())[nearest_idx]}.txt",
                    ),
                    "plot": os.path.join(
                        location,
                        directory,
                        f"calibration_uncertainty_{ifo}_{list(combined.keys())[nearest_idx]}.png",
                    ),
                }
    else:
        raise ValueError("No calibration location found")
