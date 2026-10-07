import os
from urllib.parse import urlparse, unquote
from requests_pelican import PelicanAdapter
from igwn_auth_utils import Session
import shutil
import logging

import requests

logger = logging.getLogger("gwdata")


def download_file(url, directory="frames", name=None):
    """
    Download a file from a URL.

    Parameters
    ----------
    url : str
      The URL of the file to be downloaded.
    name: str, optional
      The name the file should be saved as.
      Defaults to the name of the file on the remote resource.
    directory : str, optional
      The name of the directory in which to store the
      downloaded file. Defaults to "frames".
    """
    os.makedirs(directory, exist_ok=True)
    parsed_url = urlparse(url)
    if not name:
        local_filename = os.path.basename(parsed_url.path)
    else:
        local_filename = name

    if os.path.exists(os.path.join(directory, local_filename)):
        logger.debug(f"{local_filename} already exists in {directory}; not downloading.")
    else:
        logger.info(f"Downloading {url} to {os.path.join(directory, local_filename)}")
        if parsed_url.scheme == "file":
            shutil.copyfile(url[16:], os.path.join(directory, local_filename))
        elif parsed_url.scheme == "osdf":
            with Session() as sess:
                sess.mount("osdf://", PelicanAdapter("osdf"))
                with sess.get(url, stream=True,  token_scope="read:/ligo read:/virgo read:/kagra read:/frames read:/shared") as r:
                    with open(os.path.join(directory, local_filename), "wb") as f:
                        shutil.copyfileobj(r.raw, f)

        else:
            with requests.get(url, stream=True) as r:
                with open(os.path.join(directory, local_filename), "wb") as f:
                    shutil.copyfileobj(r.raw, f)

    return local_filename


def download_from_zenodo(record_id, directory="data", files=None):
    """
    Download files from a Zenodo record, for example a set of ROQ bases.

    Parameters
    ----------
    record_id : int
      The Zenodo record ID to download files from.
    directory : str, optional
      The name of the directory in which to store the
      downloaded files. Defaults to "data".
    files : list of str, optional
      A list of specific file names to download from the record. If None,
      all files in the record will be downloaded. Defaults to None.

    Returns
    -------
    downloaded_files : list of str
      The local paths of the downloaded files.
    """
    api_url = f"https://zenodo.org/api/records/{record_id}"
    logger.info(f"Querying Zenodo record {record_id}")
    response = requests.get(api_url)
    response.raise_for_status()
    record_files = response.json().get("files", [])
    logger.debug(f"Zenodo record {record_id} contains {len(record_files)} file(s)")

    downloaded_files = []
    for file_info in record_files:
        filename = unquote(file_info.get("key"))
        if files is not None and filename not in files:
            continue
        file_url = file_info.get("links", {}).get("self")
        local_filename = download_file(file_url, directory=directory, name=filename)
        downloaded_files.append(os.path.join(directory, local_filename))

    if files is not None:
        missing = set(files) - {os.path.basename(f) for f in downloaded_files}
        if missing:
            logger.warning(f"Files not found in Zenodo record {record_id}: {sorted(missing)}")
    logger.info(f"Downloaded {len(downloaded_files)} file(s) from Zenodo record {record_id}")
    return downloaded_files
