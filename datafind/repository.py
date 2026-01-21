"""
Manager for the asimov-data repository.

This module handles cloning, caching, and accessing blueprints from the
asimov-data repository.
"""

import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
import yaml

logger = logging.getLogger("gwdata.repository")


class AsimovDataRepository:
    """
    Manages local cache of asimov-data blueprints.

    The repository is cloned to ~/.asimov/gwdata/asimov-data/ on first use
    and can be updated on demand. Users can override the location by setting
    the ASIMOV_DATA_PATH environment variable.

    Attributes:
        cache_dir: Base cache directory (~/.asimov/gwdata/)
        repo_dir: Asimov-data repository directory
        remote_url: Git URL for the asimov-data repository
    """

    DEFAULT_REMOTE = "https://git.ligo.org/asimov/data.git"
    UPDATE_INTERVAL = timedelta(days=7)  # Check for updates weekly

    def __init__(self, remote_url=None):
        """
        Initialize the repository manager.

        Args:
            remote_url: Optional custom remote URL (defaults to official repo)
        """
        self.cache_dir = Path.home() / ".asimov" / "gwdata"
        self.repo_dir = self.cache_dir / "asimov-data"
        self.remote_url = remote_url or self.DEFAULT_REMOTE
        self.metadata_file = self.cache_dir / "metadata.yaml"

    def ensure_available(self, update=False):
        """
        Ensure the repository is available locally.

        Args:
            update: Force update even if recently updated

        Returns:
            Path to the repository directory
        """
        # Check for user override
        override_path = os.environ.get("ASIMOV_DATA_PATH")
        if override_path:
            override = Path(override_path)
            if not override.exists():
                logger.warning(
                    f"ASIMOV_DATA_PATH set to {override_path} but directory does not exist"
                )
            else:
                logger.info(f"Using asimov-data from: {override_path}")
                return override

        # Clone if not exists
        if not self.repo_dir.exists():
            logger.info("Asimov-data repository not found locally, cloning...")
            self._clone()
            return self.repo_dir

        # Update if requested or stale
        if update or self._needs_update():
            logger.info("Updating asimov-data repository...")
            self._update()

        return self.repo_dir

    def _clone(self):
        """Clone the repository."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                ["git", "clone", self.remote_url, str(self.repo_dir)],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"Successfully cloned asimov-data to {self.repo_dir}")
            self._update_metadata()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e.stderr}")
            raise RuntimeError(
                f"Could not clone asimov-data from {self.remote_url}. "
                f"Check your network connection and Git credentials."
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Git is not installed or not in PATH. Please install Git to use this feature."
            )

    def _update(self):
        """Update the repository with git pull."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_dir), "pull"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("Successfully updated asimov-data")
            self._update_metadata()
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to update repository: {e.stderr}")
            logger.info("Continuing with cached version")

    def _needs_update(self):
        """Check if repository needs updating based on metadata."""
        if not self.metadata_file.exists():
            return True

        try:
            with open(self.metadata_file, "r") as f:
                metadata = yaml.safe_load(f)

            last_update = datetime.fromisoformat(metadata.get("last_update", ""))
            return datetime.now() - last_update > self.UPDATE_INTERVAL
        except Exception as e:
            logger.debug(f"Could not read metadata: {e}")
            return False

    def _update_metadata(self):
        """Update metadata file with last update time."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        metadata = {
            "last_update": datetime.now().isoformat(),
            "remote_url": self.remote_url,
        }
        with open(self.metadata_file, "w") as f:
            yaml.dump(metadata, f)

    def list_events(self, catalog=None):
        """
        List available event blueprints.

        Args:
            catalog: Filter by catalog (gwtc-2-1, gwtc-3, ias, or None for all)

        Returns:
            List of dicts with event information
        """
        repo = self.ensure_available()
        events_dir = repo / "events"

        if not events_dir.exists():
            logger.warning(f"Events directory not found in {repo}")
            return []

        events = []

        # Determine which catalogs to search
        if catalog:
            catalogs = [catalog]
        else:
            catalogs = ["gwtc-2-1", "gwtc-3", "ias"]

        for cat in catalogs:
            cat_dir = events_dir / cat
            if not cat_dir.exists():
                continue

            for event_file in cat_dir.glob("*.yaml"):
                # Skip bulk files
                if "events.yaml" in event_file.name:
                    continue

                try:
                    with open(event_file, "r") as f:
                        event_data = yaml.safe_load(f)

                    if event_data.get("kind") == "event":
                        events.append({
                            "name": event_data.get("name", event_file.stem),
                            "catalog": cat,
                            "file": event_file,
                            "time": event_data.get("event time"),
                            "ifos": event_data.get("interferometers", []),
                        })
                except Exception as e:
                    logger.debug(f"Could not parse {event_file}: {e}")

        return sorted(events, key=lambda x: x.get("time", 0))

    def get_event(self, name):
        """
        Get event blueprint by name.

        Args:
            name: Event name (e.g., GW150914_095045)

        Returns:
            Dict with event data and file path, or None if not found
        """
        events = self.list_events()
        for event in events:
            if event["name"] == name:
                # Load full event data
                with open(event["file"], "r") as f:
                    event_data = yaml.safe_load(f)
                return {
                    "data": event_data,
                    "file": event["file"],
                    "catalog": event["catalog"],
                }
        return None

    def list_analyses(self, analysis_type=None):
        """
        List available analysis templates.

        Args:
            analysis_type: Filter by type (bilby, bayeswave, rift, or None for all)

        Returns:
            List of dicts with analysis information
        """
        repo = self.ensure_available()
        analyses_dir = repo / "analyses"

        if not analyses_dir.exists():
            logger.warning(f"Analyses directory not found in {repo}")
            return []

        analyses = []

        # Search in root analyses directory
        for analysis_file in analyses_dir.glob("*.yaml"):
            try:
                with open(analysis_file, "r") as f:
                    analysis_data = yaml.safe_load(f)

                if isinstance(analysis_data, list):
                    # Multiple analyses in one file
                    for item in analysis_data:
                        if item.get("kind") == "analysis":
                            analyses.append({
                                "name": item.get("name", analysis_file.stem),
                                "type": self._infer_type(item),
                                "file": analysis_file,
                                "pipeline": item.get("pipeline"),
                            })
                elif analysis_data.get("kind") == "analysis":
                    analyses.append({
                        "name": analysis_data.get("name", analysis_file.stem),
                        "type": self._infer_type(analysis_data),
                        "file": analysis_file,
                        "pipeline": analysis_data.get("pipeline"),
                    })
            except Exception as e:
                logger.debug(f"Could not parse {analysis_file}: {e}")

        # Search in subdirectories
        for subdir in analyses_dir.iterdir():
            if subdir.is_dir():
                for analysis_file in subdir.glob("*.yaml"):
                    try:
                        with open(analysis_file, "r") as f:
                            analysis_data = yaml.safe_load(f)

                        if analysis_data.get("kind") == "analysis":
                            analyses.append({
                                "name": analysis_data.get("name", analysis_file.stem),
                                "type": subdir.name,
                                "file": analysis_file,
                                "pipeline": analysis_data.get("pipeline"),
                            })
                    except Exception as e:
                        logger.debug(f"Could not parse {analysis_file}: {e}")

        # Filter by type if specified
        if analysis_type:
            analyses = [a for a in analyses if analysis_type in str(a.get("type", "")).lower()]

        return analyses

    def get_analysis(self, name):
        """
        Get analysis blueprint by name.

        Args:
            name: Analysis name or file stem

        Returns:
            Dict with analysis data and file path, or None if not found
        """
        analyses = self.list_analyses()
        for analysis in analyses:
            if analysis["name"] == name or analysis["file"].stem == name:
                # Load full analysis data (including multi-document YAML)
                with open(analysis["file"], "r") as f:
                    # Use safe_load_all to handle multi-document YAML
                    docs = list(yaml.safe_load_all(f))
                    # If multiple documents, return all
                    if len(docs) > 1:
                        analysis_data = docs
                    else:
                        analysis_data = docs[0] if docs else None

                return {
                    "data": analysis_data,
                    "file": analysis["file"],
                    "type": analysis["type"],
                }
        return None

    def list_bundles(self):
        """
        List available analysis bundles.

        Returns:
            List of dicts with bundle information
        """
        repo = self.ensure_available()
        bundles_dir = repo / "analyses" / "bundles"

        if not bundles_dir.exists():
            logger.debug(f"Bundles directory not found in {repo}")
            return []

        bundles = []
        for bundle_file in bundles_dir.glob("*.yaml"):
            try:
                with open(bundle_file, "r") as f:
                    bundle_data = yaml.safe_load(f)

                if bundle_data and bundle_data.get("kind") == "analysisbundle":
                    bundles.append({
                        "name": bundle_data.get("name", bundle_file.stem),
                        "description": bundle_data.get("description", ""),
                        "comment": bundle_data.get("comment", ""),
                        "analyses": bundle_data.get("analyses", []),
                        "file": bundle_file,
                    })
            except Exception as e:
                logger.debug(f"Could not parse {bundle_file}: {e}")

        return bundles

    def get_bundle(self, name):
        """
        Get bundle by name or file stem.

        Args:
            name: Bundle name or file stem

        Returns:
            Dict with bundle data and file path, or None if not found
        """
        bundles = self.list_bundles()
        for bundle in bundles:
            if bundle["name"] == name or bundle["file"].stem == name:
                with open(bundle["file"], "r") as f:
                    bundle_data = yaml.safe_load(f)

                return {
                    "data": bundle_data,
                    "file": bundle["file"],
                    "name": bundle["name"],
                    "description": bundle.get("description", ""),
                    "analyses": bundle.get("analyses", []),
                }
        return None

    def list_defaults(self):
        """
        List available default configurations.

        Returns:
            List of dicts with default configuration information
        """
        repo = self.ensure_available()
        defaults_dir = repo / "defaults"

        if not defaults_dir.exists():
            logger.warning(f"Defaults directory not found in {repo}")
            return []

        defaults = []
        for default_file in defaults_dir.glob("*.yaml"):
            try:
                with open(default_file, "r") as f:
                    default_data = yaml.safe_load(f)

                defaults.append({
                    "name": default_file.stem,
                    "file": default_file,
                    "kind": default_data.get("kind", "configuration"),
                })
            except Exception as e:
                logger.debug(f"Could not parse {default_file}: {e}")

        return defaults

    def get_default(self, name):
        """
        Get default configuration by name.

        Args:
            name: Default name (e.g., production-pe, production-pe-priors)

        Returns:
            Path to the default file, or None if not found
        """
        defaults = self.list_defaults()
        for default in defaults:
            if default["name"] == name:
                return default["file"]
        return None

    @staticmethod
    def _infer_type(analysis_data):
        """Infer analysis type from pipeline name."""
        pipeline = analysis_data.get("pipeline", "").lower()
        if "bilby" in pipeline:
            return "bilby"
        elif "bayeswave" in pipeline:
            return "bayeswave"
        elif "rift" in pipeline:
            return "rift"
        else:
            return "other"


# Singleton instance
_repository = None


def get_repository():
    """Get or create the global repository instance."""
    global _repository
    if _repository is None:
        _repository = AsimovDataRepository()
    return _repository
