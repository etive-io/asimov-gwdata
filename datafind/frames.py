"""
Data find logic for locating frame files.
"""

from gwosc.locate import get_urls
from gwdatafind import find_urls, Session
from .utils import download_file


def get_data_frames_private(types,
                            start, end,
                            download=False,
                            host="datafind.igwn.org"):
    """
    Gather data frames which are not available via GWOSC.

    Parameters
    ----------
    types : list
      The list of frame types to search for.
    start : int
      The starting GPS time.
    end : int
      The ending GPS time.
    download : bool, optional
      Choose whether to download the frame files, or
      simply return the URL.
      Defaults to False (will not download the files.)

    Returns
    -------
    urls : dict
      The dictionary of urls indexed by the detector name.
    files : dict
      The dictionary of downloaded files indexed by detector name.
    """

    urls = {}
    files = {}

    detectors = [type.split(":")[0] for type in types]
    with Session() as sess:
        for ifo, type in zip(detectors, types):
            urls[ifo] = find_urls(
                ifo[0],
                type.split(":")[-1],
                start,
                end,
                host=host,
                session=sess,
            )
    if download:
        for ifo, det_urls in urls.items():
            for url in det_urls:
                files[ifo] = download_file(url, directory="frames")
    return urls, files


def get_data_frames_gwosc(detectors, start, end, duration):
    """
    Get data frames from GWOSC.
    """
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
