from gwosc.locate import get_urls
import click

import requests
import shutil

import yaml

def download_file(url):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename

@click.command()
@click.option("--settings")
def get_data(settings): #detectors, start, end, duration, frames):
    with open(settings, "r") as file_handle:
        settings = yaml.safe_load(file_handle)

    if "frames" in settings['data']:
        get_data_frames(settings['interferometers'], settings['time']['start'], settings['time']['end'], settings['time']['duration'])

def get_data_frames(detectors, start, end, duration):
    urls = {}
    files = {}
    for detector in detectors:
        det_urls = get_urls(detector=detector,
                                  start=start,
                                  end=end,
                                  sample_rate=16384)
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
