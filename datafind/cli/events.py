"""
Event-related CLI commands.
"""

import click
from ..repository import get_repository

# Check Click version for compatibility
CLICK_VERSION = tuple(int(x) for x in click.__version__.split('.')[:2])
COMPLETION_PARAM = 'shell_complete' if CLICK_VERSION >= (8, 0) else 'autocompletion'


def complete_event_name(ctx, param, incomplete):
    """Shell completion for event names."""
    try:
        repo = get_repository()
        repo.ensure_available()
        events = repo.list_events()
        return [e["name"] for e in events if e["name"].startswith(incomplete)]
    except Exception:
        return []


def complete_analysis_name(ctx, param, incomplete):
    """Shell completion for analysis names."""
    try:
        repo = get_repository()
        repo.ensure_available()
        analyses = repo.list_analyses()
        # Include both analysis names and file stems
        names = set()
        for a in analyses:
            names.add(a["name"])
            names.add(a["file"].stem)
        return [name for name in names if name.startswith(incomplete)]
    except Exception:
        return []


@click.group(name="events")
def events():
    """
    Browse and manage GW events.

    List available events from GWTC catalogs, view event details,
    and add events to asimov projects.
    """
    pass


@events.command(name="list")
@click.option(
    "--catalog",
    type=click.Choice(["gwtc-2-1", "gwtc-3", "ias", "all"], case_sensitive=False),
    default="all",
    help="Filter by catalog",
)
@click.option("--update", is_flag=True, help="Update local repository cache")
def list_events(catalog, update):
    """
    List available gravitational wave events.

    Shows events from the asimov-data repository, organized by catalog.
    """
    repo = get_repository()

    try:
        # Ensure repository is available
        if update:
            click.echo("Updating asimov-data repository...")
        repo.ensure_available(update=update)

        # Get events
        catalog_filter = None if catalog == "all" else catalog
        events_list = repo.list_events(catalog=catalog_filter)

        if not events_list:
            click.echo("No events found.")
            return

        # Group by catalog
        by_catalog = {}
        for event in events_list:
            cat = event["catalog"]
            if cat not in by_catalog:
                by_catalog[cat] = []
            by_catalog[cat].append(event)

        # Display events
        for cat, cat_events in sorted(by_catalog.items()):
            click.echo(
                click.style(f"\n{cat.upper()} Events ({len(cat_events)} total)", bold=True)
            )
            click.echo("=" * 60)

            for event in cat_events:
                # Format IFOs
                ifos = event.get("ifos", [])
                ifo_str = ",".join(ifos) if ifos else "Unknown"

                # Print event line (just name and IFOs, no date)
                click.echo(
                    f"  {click.style(event['name'], fg='cyan', bold=True):30} "
                    f"{ifo_str}"
                )

        click.echo(f"\nTotal: {len(events_list)} events")
        click.echo(f"\nUse 'asimov gw events show <name>' for details")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()


@events.command(name="show")
@click.argument("name", **{COMPLETION_PARAM: complete_event_name})
def show_event(name):
    """
    Show detailed information about an event.

    NAME: Event name (e.g., GW150914_095045)
    """
    repo = get_repository()

    try:
        repo.ensure_available()
        event = repo.get_event(name)

        if not event:
            click.echo(click.style(f"Event '{name}' not found.", fg="red"), err=True)
            click.echo("\nUse 'asimov gw events list' to see available events.")
            raise click.Abort()

        event_data = event["data"]

        # Header
        click.echo(click.style(f"\nEvent: {name}", bold=True, fg="cyan"))
        click.echo("=" * 60)

        # Basic info
        click.echo(click.style("\nBasic Information:", bold=True))
        click.echo(f"  Catalog: {event['catalog']}")

        if "event time" in event_data:
            gps_time = event_data["event time"]
            click.echo(f"  GPS Time: {gps_time}")

        if "interferometers" in event_data:
            ifos = event_data["interferometers"]
            click.echo(f"  Interferometers: {', '.join(ifos)}")

        # Data configuration
        if "data" in event_data:
            click.echo(click.style("\nData Configuration:", bold=True))
            data = event_data["data"]

            if "channels" in data:
                click.echo("  Channels:")
                for ifo, channel in data["channels"].items():
                    click.echo(f"    {ifo}: {channel}")

            if "frame types" in data:
                click.echo("  Frame Types:")
                for ifo, frame_type in data["frame types"].items():
                    click.echo(f"    {ifo}: {frame_type}")

        # Likelihood settings
        if "likelihood" in event_data:
            click.echo(click.style("\nLikelihood Settings:", bold=True))
            likelihood = event_data["likelihood"]

            if "sample rate" in likelihood:
                click.echo(f"  Sample Rate: {likelihood['sample rate']} Hz")
            if "psd length" in likelihood:
                click.echo(f"  PSD Length: {likelihood['psd length']} s")
            if "segment length" in likelihood:
                click.echo(f"  Segment Length: {likelihood['segment length']} s")

        # Quality settings
        if "quality" in event_data:
            click.echo(click.style("\nQuality Settings:", bold=True))
            quality = event_data["quality"]

            if "minimum frequency" in quality:
                min_freq = quality["minimum frequency"]
                if isinstance(min_freq, dict):
                    click.echo("  Minimum Frequency:")
                    for ifo, freq in min_freq.items():
                        click.echo(f"    {ifo}: {freq} Hz")
                else:
                    click.echo(f"  Minimum Frequency: {min_freq} Hz")

        # Priors
        if "priors" in event_data:
            click.echo(click.style("\nPrior Configuration:", bold=True))
            priors = event_data["priors"]

            if "chirp mass" in priors:
                mc = priors["chirp mass"]
                click.echo(f"  Chirp Mass: {mc}")
            if "mass ratio" in priors:
                q = priors["mass ratio"]
                click.echo(f"  Mass Ratio: {q}")
            if "luminosity distance" in priors:
                dl = priors["luminosity distance"]
                click.echo(f"  Luminosity Distance: {dl}")

        # File location
        click.echo(click.style("\nBlueprint File:", bold=True))
        click.echo(f"  {event['file']}")

        # Usage examples
        click.echo(click.style("\nUsage:", bold=True))
        click.echo("\n  New project:")
        click.echo(f"    asimov gw setup --name my-project --events {name}")
        click.echo("\n  Add to existing project:")
        click.echo(f"    asimov gw events add {name} --analyses production-default")
        click.echo("\n  Manual application:")
        click.echo(f"    asimov apply -f {event['file']}")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()


@events.command(name="add")
@click.argument("name", **{COMPLETION_PARAM: complete_event_name})
@click.option(
    "--analyses",
    help="Comma-separated list of analyses to apply (optional)",
    **{COMPLETION_PARAM: complete_analysis_name}
)
@click.option("--dry-run", is_flag=True, help="Show what would be done without doing it")
def add_event(name, analyses, dry_run):
    """
    Add an event to the current asimov project.

    NAME: Event name (e.g., GW150914_095045)

    This command applies the event blueprint. Optionally, you can also add
    analyses to the event using the --analyses option.

    Must be run from within an asimov project directory.

    Examples:

        # Add event only (configure analyses later)
        asimov gw events add GW150914_095045

        # Add event with analyses
        asimov gw events add GW150914_095045 --analyses production-default

        # Add multiple analyses
        asimov gw events add GW150914_095045 --analyses bilby-IMRPhenomXPHM,bayeswave-psd
    """
    import os
    import subprocess

    # Check if we're in an asimov project
    if not os.path.exists(".asimov"):
        click.echo(
            click.style("Error: Not in an asimov project directory.", fg="red"), err=True
        )
        click.echo("Run 'asimov init' first or cd to an existing project.")
        raise click.Abort()

    repo = get_repository()

    try:
        repo.ensure_available()
        event = repo.get_event(name)

        if not event:
            click.echo(click.style(f"Event '{name}' not found.", fg="red"), err=True)
            raise click.Abort()

        event_file = event["file"]

        # Apply event
        cmd_event = ["asimov", "apply", "-f", str(event_file)]
        click.echo(f"Would run: {' '.join(cmd_event)}" if dry_run else f"Applying event {name}...")

        if not dry_run:
            result = subprocess.run(cmd_event, capture_output=True, text=True)
            if result.returncode != 0:
                click.echo(click.style(f"Failed to apply event", fg="red"), err=True)
                click.echo(result.stderr)
                raise click.Abort()

            # Check if event was actually added or already existed
            if "already exists" in result.stdout:
                click.echo(click.style(f"✗ {name} already exists in this project", fg="red"))
                return  # Exit cleanly without showing "Error: Aborted!"
            elif "Successfully added" in result.stdout or "Successfully updated" in result.stdout:
                click.echo(click.style(f"✓ Added event {name}", fg="green"))
            else:
                # Unexpected output, show it to user
                click.echo(result.stdout)

        # Apply analyses if specified
        if analyses:
            analysis_list = [a.strip() for a in analyses.split(",")]

            for analysis_name in analysis_list:
                analysis = repo.get_analysis(analysis_name)

                if not analysis:
                    click.echo(
                        click.style(f"Warning: Analysis '{analysis_name}' not found, skipping.", fg="yellow")
                    )
                    continue

                analysis_file = analysis["file"]
                cmd_analysis = ["asimov", "apply", "-f", str(analysis_file), "-e", name]

                click.echo(
                    f"Would run: {' '.join(cmd_analysis)}" if dry_run
                    else f"Applying analysis {analysis_name} to {name}..."
                )

                if not dry_run:
                    result = subprocess.run(cmd_analysis, capture_output=True, text=True)
                    if result.returncode != 0:
                        click.echo(
                            click.style(f"Failed to apply analysis", fg="red"),
                            err=True
                        )
                        click.echo(result.stderr)
                        raise click.Abort()

                    # Check if analysis was actually added or already existed
                    if "already exists" in result.stdout:
                        click.echo(click.style(f"✗ {analysis_name} already exists for this event", fg="yellow"))
                    elif "Successfully applied" in result.stdout:
                        click.echo(click.style(f"✓ Applied {analysis_name}", fg="green"))
                    else:
                        # Unexpected output, show it to user
                        click.echo(result.stdout)

        if not dry_run:
            click.echo(click.style("\n✓ Event added successfully!", fg="green", bold=True))

            # Only show build/submit steps if analyses were added
            if analyses:
                click.echo("\nNext steps:")
                click.echo("  asimov manage build    # Generate INI files")
                click.echo("  asimov manage submit   # Submit jobs")
            else:
                click.echo("\nNext steps:")
                click.echo(f"  asimov gw events add {name} --analyses <analysis>  # Add analyses")
                click.echo(f"  Or: asimov apply -f <analysis.yaml> -e {name}       # Manually apply analysis")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()
