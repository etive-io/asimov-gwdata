import configparser
import importlib.resources
import os
import glob
import pprint
import shutil

import asimov.pipeline

from asimov import config
from asimov.scheduler import JobDescription
from asimov.utils import set_directory


class Pipeline(asimov.pipeline.Pipeline):
    """
    An asimov pipeline for datafind.
    """

    name = "gwdata"
    config_template = importlib.resources.files("datafind").joinpath("datafind_template.yml")
    _pipeline_command = "gwdata"

    #: Every data product this pipeline can produce (asimov >= 0.8 uses this
    #: to check ``needs:`` dependencies and to find PSDs from a dependency).
    #: These are the keys :meth:`collect_assets` returns. The products a
    #: particular analysis will produce depend on its ``download`` list; see
    #: :meth:`get_actual_outputs`.
    available_outputs = ["frames", "caches", "psds", "xml psds", "calibration", "samples"]
    required_inputs = []

    # Maps entries in an analysis's ``download`` list onto output products.
    # "xml psds" is deliberately not promised for a PSD download: it is only
    # produced when convert_psd_ascii2xml is available in the job's
    # environment. Frame caches are handled in get_actual_outputs.
    _DOWNLOAD_OUTPUTS = {
        "frames": ["frames"],
        "calibration": ["calibration"],
        "psds": ["psds"],
        "psd": ["psds"],
        "posterior": ["samples"],
    }

    def get_actual_outputs(self, production):
        """
        Return the data products a specific analysis will produce,
        based on its ``download`` list (which defaults to frames, as in
        the config template).
        """
        downloads = production.meta.get("download", ["frames"]) or []
        outputs = []
        for item in downloads:
            for product in self._DOWNLOAD_OUTPUTS.get(item, []):
                if product not in outputs:
                    outputs.append(product)
        # A frame cache is only written for frames fetched from GWOSC (the
        # default), not for frames found through a datafind server (OSDF).
        source = production.meta.get("source", {}) or {}
        if "frames" in outputs and source.get("frames", "gwosc") != "osdf":
            outputs.insert(outputs.index("frames") + 1, "caches")
        return outputs

    def get_actual_inputs(self, production):
        return []

    def _accounting(self):
        """
        Work out the HTCondor accounting group and user for this job.

        The analysis's own ``scheduler: accounting group`` takes precedence,
        falling back to the project-wide ``[condor] accounting`` setting,
        which is what asimov's other pipelines use. LIGO Data Grid pools
        reject jobs without a valid accounting group, so falling back to the
        project setting matters there.

        Returns
        -------
        tuple
            ``(accounting_group, accounting_group_user)``; either may be
            ``None`` if it is not configured anywhere.
        """
        scheduler_meta = self.production.meta.get("scheduler", {}) or {}

        group = scheduler_meta.get("accounting group")
        if not group:
            try:
                group = config.get("condor", "accounting")
            except (configparser.NoOptionError, configparser.NoSectionError, KeyError):
                group = None

        user = scheduler_meta.get("accounting group user")
        if not user:
            try:
                user = config.get("condor", "user")
            except (configparser.NoOptionError, configparser.NoSectionError, KeyError):
                user = None

        return group, user

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
        Create a scheduler job description and submit it.

        With ``dryrun=True`` the submit description and wrapper script are
        still written to the run directory, so they can be inspected, but
        nothing is submitted to the scheduler.
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

        job_kwargs = {
            "batch_name": f"gwdata/{name}",
            "+flock_local": "True",
            "+DESIRED_Sites": '"none"',
            "environment": "BEARER_TOKEN_FILE=$$(CondorScratchDir)/.condor_creds/scitokens.use",
        }

        source = self.production.meta.get("source", {})
        if (source.get("type") == "frame") or (source.get("frames") == "osdf"):
            job_kwargs["use_oauth_services"] = "scitokens"

        accounting_group, accounting_group_user = self._accounting()

        if accounting_group:
            job_kwargs["accounting_group"] = accounting_group
            if accounting_group_user:
                job_kwargs["accounting_group_user"] = accounting_group_user
        else:
            self.logger.warning(
                "This job does not supply any accounting information, which may prevent it running on some clusters."
            )

        job = JobDescription(
            executable=executable,
            arguments=" ".join(command),
            output=f"{name}.out",
            error=f"{name}.err",
            log=f"{name}.log",
            memory=self.production.meta.get("scheduler", {}).get("request memory", "1024MB"),
            disk=self.production.meta.get("scheduler", {}).get("request disk", "1024MB"),
            **job_kwargs,
        )

        os.makedirs(self.production.rundir, exist_ok=True)
        with set_directory(self.production.rundir):
            with open(f"{name}.sub", "w") as subfile:
                subfile.write(
                    "\n".join(f"{key} = {value}" for key, value in job.to_htcondor().items())
                )

            full_command = f"""#! /bin/bash
{ full_command }
"""

            with open(f"{name}.sh", "w") as bashfile:
                bashfile.write(str(full_command))

        if dryrun:
            self.logger.info(
                f"Dry run: wrote {name}.sub and {name}.sh in "
                f"{self.production.rundir}, but did not submit the job."
            )
            return

        with set_directory(self.production.rundir):
            cluster_id = self.scheduler.submit(job)
            self.logger.info(f"Submitted {cluster_id} to the job queue.")

        self.production.job_id = int(cluster_id)
        self.clusterid = cluster_id

    def submit_dag(self, dryrun=False):
        if dryrun:
            self.logger.info(
                f"Dry run: not marking {self.production.name} as running, "
                "since no job was submitted."
            )
            return None
        self.production.status = "running"
        self.production.job_id = int(self.clusterid)
        return self.clusterid

    def detect_completion(self):
        self.logger.info("Checking for completion.")
        assets = self.collect_assets()
        settings = self.production.meta
        downloads = set(settings.get("download", []))

        event_settings = self.production.event.meta
        if len(list(assets.keys())) > 0:
            self.logger.info("Outputs detected, job complete.")
            return True
        elif (downloads == {"calibration"}) \
                and ("V1" in settings.get("interferometers", {})) \
                and ("V1" not in event_settings.get("interferometers", {})):
            self.logger.info("Virgo calibration data are not required for the event.")
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
        settings = self.production.meta
        if os.path.exists(os.path.join(self.production.rundir, "frames")) and ("frames" in settings.get("download", [])):
            results_dir = sorted(glob.glob(os.path.join(self.production.rundir, "frames", "*")))
            frames = {}

            for frame in results_dir:
                ifo = frame.split("/")[-1].split("_")[0].split("-")[0]+"1"
                if ifo not in frames:
                    frames[ifo] = []
                frames[ifo].append(frame)

            outputs["frames"] = frames

            event_data = self.production.event.meta.setdefault("data", {})
            event_data.setdefault("data files", {}).update(frames)


        if os.path.exists(os.path.join(self.production.rundir, "cache")) and (
            "frames" in settings.get("download", [])
        ):
            results_dir = glob.glob(os.path.join(self.production.rundir, "cache", "*"))
            cache = {}

            for cache_file in results_dir:
                ifo = cache_file.split("/")[-1].split(".")[0]
                cache[ifo] = cache_file

            outputs["caches"] = cache
            self.production.event.meta.setdefault("data", {})["cache files"] = cache

        if os.path.exists(os.path.join(self.production.rundir, "psds")):
            results_dir = glob.glob(os.path.join(self.production.rundir, "psds", "*.dat"))
            psds = {}

            for psd in results_dir:
                ifo = os.path.splitext(os.path.basename(psd))[0]
                psds[ifo] = psd

            outputs["psds"] = psds
            self.production.event.meta["psds"] = psds

            results_dir = glob.glob(os.path.join(self.production.rundir, "psds", "*.xml.gz"))
            xml_psds = {}

            for psd in results_dir:
                ifo = os.path.splitext(os.path.basename(psd))[0]
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

            event_data = self.production.event.meta.setdefault("data", {})
            event_data.setdefault("calibration", {}).update(calibration)
            
        if os.path.exists(os.path.join(self.production.rundir, "posterior")):
            results = glob.glob(os.path.join(self.production.rundir, "posterior", "*"))

            outputs["samples"] = results[0]

        return outputs

    def html(self):
        """Return the HTML representation of this pipeline."""
        out = ""

        webdir = os.path.join(
                config.get("project", "root"),
                config.get("general", "webroot"),
                self.production.event.name,
                self.production.name
            )

        if os.path.exists(os.path.join(self.production.rundir, "report")):
            # copytree creates `webdir` (and any missing parents) itself,
            # so there's no need to pre-create it - and no report dir means
            # nothing to copy, so `webdir` shouldn't be created at all just
            # from viewing the project page.
            shutil.copytree(
                os.path.join(self.production.rundir, "report"),
                webdir,
                dirs_exist_ok=True
            )
            pages_dir = os.path.join(
                self.production.event.name, self.production.name
            )

            out += f"<p><a href='{pages_dir}'>Summary report</a></p>"

        if self.production.status in {"finished", "uploaded"}:
            out += """<div class="asimov-pipeline">"""
            pp = pprint.PrettyPrinter(indent=4)
            out += f"<pre>{ pp.pformat(self.collect_assets()) }</pre>"
            out += """</div>"""

        return out
