import importlib
import os
import configparser
import glob

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
        data = data.replace("<gid>", self.production.event.meta['ligo']['preferred event'])
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
        executable = os.path.join(config.get('pipelines', 'environment'), 'bin', self._pipeline_command)
        command = ["--settings", ini]
        full_command = executable + " " + " ".join(command)
        self.logger.info(full_command)

        description = {
            "executable": f"{executable}",
            "arguments": f"{' '.join(command)}",
            "output": f"{name}.out",
            "error": f"{name}.err",
            "log": f"{name}.log",
            "request_disk": "1024",
            "request_memory": "1024",
            "batch_name": f"gwdata/{name}",
            "accounting_group_user": config.get('condor', 'user'),
            "accounting_group": self.production.meta['scheduler']["accounting group"],
        }

        job = htcondor.Submit(description)
        os.makedirs(self.production.rundir, exist_ok=True)
        with set_directory(self.production.rundir):
            with open(f"{name}.sub", "w") as subfile:
                subfile.write(job.__str__())
                
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
        frames = self.collect_assets()
        if len(list(frames.keys())) > 0:
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
        if os.path.exists(f"{self.production.rundir}/frames/"):
            results_dir = glob.glob(f"{self.production.rundir}/frames/*")
            frames = {}

            for frame in results_dir:
                ifo = frame.split("/")[-1].split("_")[0].split("-")[1]
                frames[ifo] = frame

            outputs["frames"] = frames

            self.production.event.meta['data']['data files'] = frames

        if os.path.exists(f"{self.production.rundir}/psds/"):
            results_dir = glob.glob(f"{self.production.rundir}/psds/*")
            psds = {}

            for psd in results_dir:
                ifo = psds.split(".")[0]
                psds[ifo] = psd

            outputs["psds"] = psds

        # TODO: Need to have this check the sample rate before it saves to ledger
        # self.production.event.meta['data']['data files'] = frames

        if os.path.exists(f"{self.production.rundir}/calibration/"):
            results_dir = glob.glob(f"{self.production.rundir}/calibration/*")
            calibration = {}

            for cal in results_dir:
                ifo = cal.split(".")[0]
                calibration[ifo] = cal

            outputs["calibration"] = calibration

            self.production.event.meta['data']['calibration'] = calibration

        if os.path.exists(f"{self.production.rundir}/posterior/"):
            results = glob.glob(f"{self.production.rundir}/posterior/*")

            outputs["samples"] = results[0]

        return outputs
