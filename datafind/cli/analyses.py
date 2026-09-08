"""
Analysis-related CLI commands.
"""

import click
import yaml
from ..repository import get_repository

# Check Click version for compatibility
CLICK_VERSION = tuple(int(x) for x in click.__version__.split('.')[:2])
COMPLETION_PARAM = 'shell_complete' if CLICK_VERSION >= (8, 0) else 'autocompletion'


def complete_analysis_name(ctx, param, incomplete):
    """Shell completion for analysis names."""
    try:
        repo = get_repository()
        repo.ensure_available()
        analyses = repo.list_analyses()
        names = set()
        for a in analyses:
            names.add(a["name"])
            names.add(a["file"].stem)
        return [name for name in names if name.startswith(incomplete)]
    except Exception:
        return []


@click.group(name="analyses")
def analyses():
    """
    Browse and manage analysis templates.

    List available analysis configurations and view their details.
    """
    pass


@analyses.command(name="list")
@click.option(
    "--type",
    "analysis_type",
    type=click.Choice(["bilby", "bayeswave", "rift", "all"], case_sensitive=False),
    default="all",
    help="Filter by analysis type",
)
@click.option("--update", is_flag=True, help="Update local repository cache")
def list_analyses(analysis_type, update):
    """
    List available analysis templates.

    Shows analysis configurations from the asimov-data repository.
    """
    repo = get_repository()

    try:
        # Ensure repository is available
        if update:
            click.echo("Updating asimov-data repository...")
        repo.ensure_available(update=update)

        # Get analyses
        type_filter = None if analysis_type == "all" else analysis_type
        analyses_list = repo.list_analyses(analysis_type=type_filter)

        if not analyses_list:
            click.echo("No analyses found.")
            return

        # Group by type
        by_type = {}
        for analysis in analyses_list:
            atype = analysis.get("type", "other")
            if atype not in by_type:
                by_type[atype] = []
            by_type[atype].append(analysis)

        # Display analyses
        for atype, type_analyses in sorted(by_type.items()):
            click.echo(
                click.style(f"\n{atype.capitalize()} Analyses ({len(type_analyses)} total)", bold=True)
            )
            click.echo("=" * 60)

            for analysis in type_analyses:
                name = analysis.get("name", "Unknown")
                pipeline = analysis.get("pipeline", "Unknown")

                click.echo(
                    f"  {click.style(name, fg='cyan', bold=True):30} "
                    f"{pipeline}"
                )

        click.echo(f"\nTotal: {len(analyses_list)} analyses")
        click.echo(f"\nUse 'asimov gw analyses show <name>' for details")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()


@analyses.command(name="show")
@click.argument("name", **{COMPLETION_PARAM: complete_analysis_name})
def show_analysis(name):
    """
    Show detailed information about an analysis.

    NAME: Analysis name (e.g., production-default)
    """
    repo = get_repository()

    try:
        repo.ensure_available()
        analysis = repo.get_analysis(name)

        if not analysis:
            click.echo(click.style(f"Analysis '{name}' not found.", fg="red"), err=True)
            click.echo("\nUse 'asimov gw analyses list' to see available analyses.")
            raise click.Abort()

        analysis_data = analysis["data"]

        # Handle list of analyses
        if isinstance(analysis_data, list):
            click.echo(click.style(f"\nAnalysis Collection: {name}", bold=True, fg="cyan"))
            click.echo("=" * 60)
            click.echo(f"\nThis file contains {len(analysis_data)} analysis configuration(s).\n")

            for idx, item in enumerate(analysis_data, 1):
                _display_single_analysis(item, idx)

        else:
            # Single analysis
            analysis_name = analysis_data.get("name", name)
            click.echo(click.style(f"\nAnalysis: {analysis_name}", bold=True, fg="cyan"))
            click.echo("=" * 60)
            _display_single_analysis(analysis_data)

        # File location
        click.echo(click.style("\nBlueprint File:", bold=True))
        click.echo(f"  {analysis['file']}")

        # Usage examples
        click.echo(click.style("\nUsage:", bold=True))
        click.echo("\n  New project:")
        click.echo(f"    asimov gw setup --name my-project --events <event> --analyses {name}")
        click.echo("\n  Add to existing project:")
        click.echo(f"    asimov gw events add <event-name> --analyses {name}")
        click.echo("\n  Manual application:")
        click.echo(f"    asimov apply -f {analysis['file']} -e <event-name>")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()


def _display_single_analysis(data, number=None):
    """Display a single analysis configuration."""
    if number:
        click.echo(click.style(f"Analysis {number}:", bold=True))

    # Basic info
    if "name" in data:
        click.echo(f"  Name: {data['name']}")
    if "pipeline" in data:
        click.echo(f"  Pipeline: {data['pipeline']}")

    # Dependencies
    if "needs" in data:
        needs = data["needs"]
        if isinstance(needs, list):
            click.echo(f"  Dependencies: {', '.join(needs)}")
        else:
            click.echo(f"  Dependencies: {needs}")

    # Waveform approximant
    if "approximant" in data:
        click.echo(f"  Waveform: {data['approximant']}")

    # Sampler settings
    if "sampler" in data:
        sampler = data["sampler"]
        if isinstance(sampler, dict):
            click.echo(f"  Sampler: {sampler.get('sampler', 'Unknown')}")
            if "nlive" in sampler:
                click.echo(f"  N Live Points: {sampler['nlive']}")
        else:
            click.echo(f"  Sampler: {sampler}")

    # Scheduler settings
    if "scheduler" in data:
        scheduler = data["scheduler"]
        if isinstance(scheduler, dict):
            if "request cpus" in scheduler:
                click.echo(f"  CPUs: {scheduler['request cpus']}")
            if "request memory" in scheduler:
                click.echo(f"  Memory: {scheduler['request memory']}")

    # Show a few key settings if present
    interesting_keys = ["calibration", "psd", "reference frequency", "duration"]
    for key in interesting_keys:
        if key in data:
            click.echo(f"  {key.title()}: {data[key]}")

    if number:
        click.echo()  # Blank line between analyses


@analyses.command(name="show-defaults")
def show_defaults():
    """
    List available default configurations.

    Shows default configurations like production-pe, production-pe-priors, etc.
    """
    repo = get_repository()

    try:
        repo.ensure_available()
        defaults = repo.list_defaults()

        if not defaults:
            click.echo("No default configurations found.")
            return

        click.echo(click.style("\nAvailable Default Configurations", bold=True))
        click.echo("=" * 60)

        for default in defaults:
            name = default["name"]
            kind = default.get("kind", "configuration")

            click.echo(f"  {click.style(name, fg='cyan', bold=True):30} ({kind})")

        click.echo(f"\nTotal: {len(defaults)} configurations")
        click.echo(f"\nThese are typically applied during project setup:")
        click.echo("  asimov apply -f <path>/production-pe.yaml")
        click.echo("  asimov apply -f <path>/production-pe-priors.yaml")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()
