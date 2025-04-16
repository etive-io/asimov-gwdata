"""
Functions and classes to facilitate interaction with GraceDB.
"""

from ligo.gracedb.rest import GraceDb, HTTPError
import subprocess

class GraceDB:

    def __init__(self, gid, gracedb_url="https://gracedb.ligo.org"):
        """
        Create a GraceDB connection for an event.
        
        Parameters
        ----------
        gid : str
           The GraceID for the event.
        """

        self.gid = gid
        self.client = GraceDb(service_url=gracedb_url)
    
    def download_file(self, gfile, destination):
        """
        Get a file from Gracedb, and store it in the event repository.

        Parameters
        ----------
        gfile : str
           The name of the gracedb file, e.g. `coinc.xml`.
        destination : str
           The location in the repository for this file.

        Notes
        -----
        This code is adapted directly from code originally contained within the main asimov codebase.
        """

        try:
            file_obj = self.client.files(self.gid, gfile)

            with open("download.file", "w") as dest_file:
                dest_file.write(file_obj.read().decode())

            if "xml" in gfile:
                # Convert to the new xml format
                command = ["ligolw_no_ilwdchar", "download.file"]
                pipe = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
                out, err = pipe.communicate()

            self.repository.add_file(
                "download.file",
                destination,
                commit_message=f"Downloaded {gfile} from GraceDB",
            )
            self.logger.info(f"Fetched {gfile} from GraceDB")
        except HTTPError as e:
            self.logger.error(
                f"Unable to connect to GraceDB when attempting to download {gfile}. {e}"
            )
            raise HTTPError(e)

