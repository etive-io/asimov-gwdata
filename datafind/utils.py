import os
import shutil

import requests


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
    if not name:
        local_filename = url.split("/")[-1]
    else:
        local_filename = name
    if url[:4] == "file":
        shutil.copyfile(url[16:], os.path.join(directory, local_filename))
    else:
        with requests.get(url, stream=True) as r:
            with open(os.path.join(directory, local_filename), "wb") as f:
                shutil.copyfileobj(r.raw, f)

    return local_filename
