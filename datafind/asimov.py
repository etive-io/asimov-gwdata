import importlib
import os
import configparser
import glob
import pprint

import asimov.pipeline

from asimov import config
import htcondor
from asimov.utils import set_directory


class Pipeline(asimov.pipeline.Pipeline):
    """
    An asimov pipeline for datafind.
    """

    name = "gwdata"
    with importlib.resources.path("datafind", "datafind_template.yml") as template_file:
        config_template = template_file
    _pipeline_command = "gwdata"

    def _substitute_locations_in_config(self):
        """
        Perform string substitutions in the config file for this pipeline.

        Notes
        -----
        This is something of a hack, to allow us to rewrite the location paths
        on the fly to prevent hard-coding things at any stage.
        """
        name = self.production.name
        ini = self.production.event.repository.find_prods(name, self.category)[0]
        with open(ini, "r") as config_file:
            data = config_file.read()
        data = data.replace("<event>", self.production.event.name)
        data = data.replace(
            "<gid>", self.production.event.meta.get("ligo", {}).get("preferred event", "")
        )
        if "illustrative result" in self.production.event.meta.get("ligo", {}):
            result = self.production.event.meta["ligo"]["illustrative result"]
        else:
            result = "online"
        if not result:
            result = "online"
        data = data.replace(
            "<illustrative_result>",
            result
        )
        self.logger.info(data)
        with open(ini, "w") as config_file:
            config_file.write(data)

    def build_dag(self, dryrun=False):
        """
        Create a condor submission description.
        """
        name = self.production.name  # meta['name']
        ini = self.production.event.repository.find_prods(name, self.category)[0]
        self._substitute_locations_in_config()
        executable = os.path.join(
            config.get("pipelines", "environment"), "bin", self._pipeline_command
        )
        command = ["--settings", ini]
        full_command = executable + " " + " ".join(command)
        self.logger.info(full_command)

        description = {
            "executable": f"{executable}",
            "arguments": f"{' '.join(command)}",
            "output": f"{name}.out",
            "error": f"{name}.err",
            "log": f"{name}.log",
            "request_disk": self.production.meta.get("scheduler", {}).get("request disk", "1024MB"),
            "request_memory": self.production.meta.get("scheduler", {}).get("request memory", "1024MB"),
            "batch_name": f"gwdata/{name}",
            "+flock_local": "True",
            "+DESIRED_Sites": htcondor.classad.quote("nogrid"),
        }

        accounting_group = self.production.meta.get("scheduler", {}).get(
            "accounting group", None
        )

        if accounting_group:
            description["accounting_group_user"] = config.get("condor", "user")
            description["accounting_group"] = accounting_group
        else:
            self.logger.warning(
                "This job does not supply any accounting information, which may prevent it running on some clusters."
            )

        job = htcondor.Submit(description)
        os.makedirs(self.production.rundir, exist_ok=True)
        with set_directory(self.production.rundir):
            with open(f"{name}.sub", "w") as subfile:
                subfile.write(job.__str__())

            full_command = f"""#! /bin/bash
{ full_command }
"""

            with open(f"{name}.sh", "w") as bashfile:
                bashfile.write(str(full_command))

        with set_directory(self.production.rundir):
            try:
                schedulers = htcondor.Collector().locate(
                    htcondor.DaemonTypes.Schedd, config.get("condor", "scheduler")
                )
            except configparser.NoOptionError:
                schedulers = htcondor.Collector().locate(htcondor.DaemonTypes.Schedd)
            schedd = htcondor.Schedd(schedulers)
            with schedd.transaction() as txn:
                cluster_id = job.queue(txn)
                self.logger.info("Submitted to htcondor job queue.")

        self.production.job_id = int(cluster_id)
        self.clusterid = cluster_id

    def submit_dag(self, dryrun=False):
        self.production.status = "running"
        self.production.job_id = int(self.clusterid)
        return self.clusterid

    def detect_completion(self):
        self.logger.info("Checking for completion.")
        assets = self.collect_assets()
        if len(list(assets.keys())) > 0:
            self.logger.info("Outputs detected, job complete.")
            return True
        else:
            self.logger.info("Datafind job completion was not detected.")
            return False

    def after_completion(self):
        self.production.status = "uploaded"
        self.production.event.update_data()

    def collect_assets(self):
        """
        Collect the assets for this job.
        """
        outputs = {}
        if os.path.exists(os.path.join(self.production.rundir, "frames")):
            results_dir = glob.glob(os.path.join(self.production.rundir, "frames", "*"))
            frames = {}

            for frame in results_dir:
                ifo = frame.split("/")[-1].split("_")[0].split("-")[1]
                frames[ifo] = frame

            outputs["frames"] = frames

            self.production.event.meta["data"]["data files"] = frames

        if os.path.exists(os.path.join(self.production.rundir, "cache")):
            results_dir = glob.glob(os.path.join(self.production.rundir, "cache", "*"))
            cache = {}

            for cache_file in results_dir:
                ifo = cache_file.split("/")[-1].split(".")[0]
                cache[ifo] = cache_file

            outputs["caches"] = cache
            self.production.event.meta['data']['cache files'] = cache
            
        if os.path.exists(os.path.join(self.production.rundir, "psds")):
            results_dir = glob.glob(os.path.join(self.production.rundir, "psds", "*.dat"))
            psds = {}

            for psd in results_dir:
                ifo = os.path.splitext(psds)[0]
                psds[ifo] = psd

            outputs["psds"] = psds
                
            results_dir = glob.glob(os.path.join(self.production.rundir, "psds", "*.xml.gz"))
            xml_psds = {}

            for psd in results_dir:
                ifo = os.path.splitext(psds)[0]
                xml_psds[ifo] = psd

            outputs["xml psds"] = xml_psds

        # TODO: Need to have this check the sample rate before it saves to ledger
        # self.production.event.meta['data']['data files'] = frames

        if os.path.exists(os.path.join(self.production.rundir, "calibration")):
            results_dir = glob.glob(
                os.path.join(self.production.rundir, "calibration", "*")
            )
            calibration = {}

            for cal in results_dir:
                ifo = os.path.splitext(cal)[0].split(os.sep)[-1]
                calibration[ifo] = cal

            outputs["calibration"] = calibration

            self.production.event.meta["data"]["calibration"] = calibration

        if os.path.exists(os.path.join(self.production.rundir, "posterior")):
            results = glob.glob(os.path.join(self.production.rundir, "posterior", "*"))

            outputs["samples"] = results[0]

        return outputs

    def html(self):
        """Return the HTML representation of this pipeline."""
        out = ""
        if self.production.status in {"finished", "uploaded"}:
            out += """<div class="asimov-pipeline">"""
            pp = pprint.PrettyPrinter(indent=4)
            out += f"<pre>{ pp.pformat(self.collect_assets()) }</pre>"
            out += """</div>"""

        return out
