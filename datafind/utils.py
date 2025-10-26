import os
from urllib.parse import urlparse, unquote
import requests
from requests_pelican import PelicanAdapter
from igwn_auth_utils import Session
import shutil

def download_from_zenodo(record_id, directory="data", files=None):
    """
    Download all files from a Zenodo record.

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
    """
    os.makedirs(directory, exist_ok=True)
    api_url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(api_url)
    response.raise_for_status()
    record = response.json()
    download_files = files if files is not None else None
    files = record.get("files", [])
    downloaded_files = []

    for file_info in files:
        file_url = file_info.get("links", {}).get("self")
        if file_url and (download_files is None or file_info.get("key") in download_files):
            filename = unquote(file_info.get("key"))
            local_path = os.path.join(directory, filename)
            if not os.path.exists(local_path):
                with requests.get(file_url, stream=True) as r:
                    r.raise_for_status()
                    with open(local_path, "wb") as f:
                        shutil.copyfileobj(r.raw, f)
            downloaded_files.append(local_path)

    return downloaded_files

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

    if not os.path.exists(os.path.join(directory, local_filename)):
                
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
