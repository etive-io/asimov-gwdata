"""
Project setup and quickstart commands.
"""

import os
import subprocess
from pathlib import Path
import click
from ..repository import get_repository

# Check Click version for compatibility
CLICK_VERSION = tuple(int(x) for x in click.__version__.split('.')[:2])
COMPLETION_PARAM = 'shell_complete' if CLICK_VERSION >= (8, 0) else 'autocompletion'


def complete_event_names_multi(ctx, param, incomplete):
    """Shell completion for comma-separated event names."""
    try:
        repo = get_repository()
        repo.ensure_available()
        events = repo.list_events()

        # Handle comma-separated values
        if ',' in incomplete:
            # Complete the part after the last comma
            prefix = incomplete.rsplit(',', 1)[0] + ','
            incomplete_part = incomplete.rsplit(',', 1)[1]
            return [prefix + e["name"] for e in events if e["name"].startswith(incomplete_part)]
        else:
            return [e["name"] for e in events if e["name"].startswith(incomplete)]
    except Exception:
        return []


def complete_analysis_names_multi(ctx, param, incomplete):
    """Shell completion for comma-separated analysis names."""
    try:
        repo = get_repository()
        repo.ensure_available()
        analyses = repo.list_analyses()
        names = set()
        for a in analyses:
            names.add(a["name"])
            names.add(a["file"].stem)

        # Handle comma-separated values
        if ',' in incomplete:
            prefix = incomplete.rsplit(',', 1)[0] + ','
            incomplete_part = incomplete.rsplit(',', 1)[1]
            return [prefix + name for name in names if name.startswith(incomplete_part)]
        else:
            return [name for name in names if name.startswith(incomplete)]
    except Exception:
        return []


@click.command(name="setup")
@click.option(
    "--name",
    required=True,
    help="Project name (required for new projects)"
)
@click.option(
    "--preset",
    type=click.Choice(["production", "testing"], case_sensitive=False),
    default="production",
    help="Configuration preset",
)
@click.option(
    "--events",
    required=True,
    help="Comma-separated list of event names",
    **{COMPLETION_PARAM: complete_event_names_multi}
)
@click.option(
    "--analyses",
    default="production-default",
    help="Comma-separated list of analyses",
    **{COMPLETION_PARAM: complete_analysis_names_multi}
)
@click.option("--directory", help="Output directory (default: current directory)")
@click.option("--dry-run", is_flag=True, help="Show what would be done without doing it")
def setup(name, preset, events, analyses, directory, dry_run):
    """
    Set up a NEW asimov project with GW events and analyses.

    This command creates a new project directory and initializes it with events
    and analyses. If you want to add events to an existing project, use:

        asimov gw events add <event> --analyses <analyses>

    The setup command automates:
    1. Initialize asimov project
    2. Apply default configurations (production-pe, priors, etc.)
    3. Add events
    4. Configure analyses

    Examples:

        # Production setup with one event
        asimov gw setup --name my-analysis --events GW150914_095045

        # Multiple events
        asimov gw setup --name gwtc3-sample \\
            --events GW150914_095045,GW151012_095443,GW151226_033853

        # Testing configuration (lighter, faster)
        asimov gw setup --name test-run --preset testing \\
            --events GW150914_095045

        # Custom analyses
        asimov gw setup --name custom --events GW150914_095045 \\
            --analyses bilby-imrphenomxphm,bayeswave-psd
    """
    repo = get_repository()

    try:
        # Ensure repository is available
        click.echo("Checking asimov-data repository...")
        repo.ensure_available()

        # Parse event and analysis lists
        event_list = [e.strip() for e in events.split(",")]
        analysis_list = [a.strip() for a in analyses.split(",")]

        # Determine project directory
        if directory:
            project_dir = Path(directory) / name
        else:
            project_dir = Path.cwd() / name

        # Show plan
        click.echo(click.style("\nProject Setup Plan", bold=True, fg="cyan"))
        click.echo("=" * 60)
        click.echo(f"Project Name: {name}")
        click.echo(f"Directory: {project_dir}")
        click.echo(f"Preset: {preset}")
        click.echo(f"Events: {', '.join(event_list)} ({len(event_list)} total)")
        click.echo(f"Analyses: {', '.join(analysis_list)}")
        click.echo()

        if dry_run:
            click.echo(click.style("DRY RUN - No changes will be made\n", fg="yellow", bold=True))

        # Step 1: Initialize project
        init_cwd = str(directory) if directory else "."
        _run_step(
            f"Initializing project '{name}'",
            ["asimov", "init", name],
            cwd=init_cwd,
            dry_run=dry_run,
        )

        # Verify project was created (check in the directory where we ran init)
        if not dry_run:
            expected_dir = Path(init_cwd) / name
            if not expected_dir.exists():
                click.echo(click.style(f"Error: Project directory {expected_dir} was not created", fg="red"), err=True)
                raise click.Abort()
            project_dir = expected_dir

        # Step 2: Apply default configurations
        defaults_to_apply = _get_defaults_for_preset(preset, repo)

        for default_name, default_file in defaults_to_apply:
            _run_step(
                f"Applying {default_name}",
                ["asimov", "apply", "-f", str(default_file)],
                cwd=str(project_dir),
                dry_run=dry_run,
            )

        # Step 3: Add events
        for event_name in event_list:
            event = repo.get_event(event_name)
            if not event:
                click.echo(
                    click.style(f"Warning: Event '{event_name}' not found, skipping", fg="yellow")
                )
                continue

            _run_step(
                f"Adding event {event_name}",
                ["asimov", "apply", "-f", str(event["file"])],
                cwd=str(project_dir),
                dry_run=dry_run,
            )

        # Step 4: Configure analyses for each event
        for analysis_name in analysis_list:
            analysis = repo.get_analysis(analysis_name)

            # If not found by analysis name, try to find by file stem
            if not analysis:
                # Try to find file by name in analyses directory
                analyses_dir = repo.repo_dir / "analyses"
                analysis_file = analyses_dir / f"{analysis_name}.yaml"
                if analysis_file.exists():
                    analysis = {
                        "file": analysis_file,
                        "name": analysis_name,
                        "type": "file",
                    }
                else:
                    click.echo(
                        click.style(f"Warning: Analysis '{analysis_name}' not found, skipping", fg="yellow")
                    )
                    continue

            for event_name in event_list:
                event = repo.get_event(event_name)
                if not event:
                    continue  # Already warned above

                _run_step(
                    f"Configuring {analysis_name} for {event_name}",
                    ["asimov", "apply", "-f", str(analysis["file"]), "-e", event_name],
                    cwd=str(project_dir),
                    dry_run=dry_run,
                )

        # Success!
        if not dry_run:
            click.echo(click.style("\n✓ Project setup complete!", fg="green", bold=True))
            click.echo(f"\nProject created at: {project_dir}")
            click.echo("\nNext steps:")
            click.echo(f"  cd {project_dir}")
            click.echo("  asimov manage build    # Generate INI configuration files")
            click.echo("  asimov manage submit   # Submit jobs to the cluster")
            click.echo("  asimov monitor         # Check job status")
        else:
            click.echo(click.style("\nDry run complete!", fg="yellow", bold=True))

    except Exception as e:
        if not isinstance(e, click.exceptions.Abort):
            click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()


@click.command(name="quickstart")
def quickstart():
    """
    Interactive wizard for setting up an asimov project.

    This wizard will guide you through:
    - Choosing a configuration preset
    - Selecting events from catalogs
    - Picking analysis pipelines
    - Setting up your project

    This is a user-friendly alternative to the 'setup' command
    for those who prefer an interactive experience.
    """
    click.echo(click.style("\nAsimov GW Analysis Quickstart Wizard", bold=True, fg="cyan"))
    click.echo("=" * 60)
    click.echo("\nThis wizard will help you set up a new asimov project.")
    click.echo()

    try:
        # Check if we have the questionary library for better UI
        try:
            import questionary
            has_questionary = True
        except ImportError:
            has_questionary = False
            click.echo(
                click.style(
                    "Tip: Install 'questionary' for a better interactive experience: pip install questionary\n",
                    fg="yellow"
                )
            )

        repo = get_repository()
        repo.ensure_available()

        # Step 1: Project name
        project_name = click.prompt("Project name", type=str)

        # Step 2: Preset
        if has_questionary:
            preset = questionary.select(
                "Select configuration preset:",
                choices=[
                    questionary.Choice("Production PE (O4a settings) - Recommended", value="production"),
                    questionary.Choice("Testing PE (lightweight, faster)", value="testing"),
                ],
            ).ask()
        else:
            click.echo("\nConfiguration presets:")
            click.echo("  1. Production PE (O4a settings) - Recommended")
            click.echo("  2. Testing PE (lightweight, faster)")
            preset_choice = click.prompt("Select preset", type=click.IntRange(1, 2), default=1)
            preset = "production" if preset_choice == 1 else "testing"

        # Step 3: Event selection
        click.echo("\nFetching available events...")
        events_list = repo.list_events()

        if not events_list:
            click.echo(click.style("No events found in repository.", fg="red"))
            raise click.Abort()

        # Group events by catalog for easier browsing
        by_catalog = {}
        for event in events_list:
            cat = event["catalog"]
            if cat not in by_catalog:
                by_catalog[cat] = []
            by_catalog[cat].append(event["name"])

        click.echo("\nAvailable catalogs:")
        catalog_choices = list(by_catalog.keys())
        for idx, cat in enumerate(catalog_choices, 1):
            click.echo(f"  {idx}. {cat.upper()} ({len(by_catalog[cat])} events)")

        catalog_idx = click.prompt("Select catalog", type=click.IntRange(1, len(catalog_choices)))
        selected_catalog = catalog_choices[catalog_idx - 1]
        catalog_events = by_catalog[selected_catalog]

        # Show events from selected catalog
        click.echo(f"\n{selected_catalog.upper()} events:")
        for idx, event_name in enumerate(catalog_events[:20], 1):  # Show first 20
            click.echo(f"  {idx}. {event_name}")
        if len(catalog_events) > 20:
            click.echo(f"  ... and {len(catalog_events) - 20} more")

        # Let user select events
        if has_questionary:
            # Can do multi-select with questionary
            selected_events = questionary.checkbox(
                "Select events (space to select, enter to continue):",
                choices=[questionary.Choice(name) for name in catalog_events],
            ).ask()

            # Handle user cancellation (Ctrl+C)
            if selected_events is None:
                click.echo("\nSetup cancelled.")
                return
        else:
            # Simple input
            event_input = click.prompt(
                "\nEnter event numbers (comma-separated) or names",
                type=str,
                default="1"
            )
            # Try to parse as numbers or names
            selected_events = []
            for item in event_input.split(","):
                item = item.strip()
                if item.isdigit():
                    idx = int(item) - 1
                    if 0 <= idx < len(catalog_events):
                        selected_events.append(catalog_events[idx])
                else:
                    # Assume it's an event name
                    if item in catalog_events:
                        selected_events.append(item)

        if not selected_events:
            click.echo(click.style("No events selected.", fg="red"))
            raise click.Abort()

        # Step 4: Analysis selection
        click.echo("\nFetching available analyses...")
        analyses_list = repo.list_analyses()
        bundles_list = repo.list_bundles()

        # Group analyses by file
        analyses_by_file = {}
        for analysis in analyses_list:
            file_stem = analysis["file"].stem
            if file_stem not in analyses_by_file:
                analyses_by_file[file_stem] = []
            analyses_by_file[file_stem].append(analysis)

        # Prepare choices: show bundles first, then multi-analysis files, then individual analyses
        choices = []

        # Add analysis bundles first (highest priority)
        for bundle in bundles_list:
            bundle_name = bundle["name"]
            analyses_refs = bundle["analyses"]
            description = bundle.get("description", "")
            if description:
                label = f"{bundle_name} (Bundle) - {description}"
            else:
                label = f"{bundle_name} (Bundle: {len(analyses_refs)} analyses)"
            choices.append({
                "value": f"bundles/{bundle['file'].stem}",  # Reference bundle file
                "label": label,
                "short": bundle_name,
                "is_bundle": True
            })

        # Add separator if we have bundles
        if bundles_list:
            choices.append({"value": "---files", "label": "--- Multi-Analysis Files ---", "short": "---", "disabled": True})

        # Add multi-analysis files (files with multiple analyses)
        multi_files = {stem: analyses for stem, analyses in analyses_by_file.items() if len(analyses) > 1}

        if "production-default" in multi_files:
            # Show production-default first with description
            analyses = multi_files["production-default"]
            description = f"Standard GWTC-3 pipeline ({len(analyses)} analyses: {', '.join([a['name'] for a in analyses])})"
            choices.append({
                "value": "production-default",
                "label": f"production-default - {description}",
                "short": "production-default"
            })

        # Add other multi-analysis files
        for stem in sorted(multi_files.keys()):
            if stem == "production-default":
                continue
            analyses = multi_files[stem]
            description = f"{len(analyses)} analyses: {', '.join([a['name'] for a in analyses[:3]])}"
            if len(analyses) > 3:
                description += "..."
            choices.append({
                "value": stem,
                "label": f"{stem} - {description}",
                "short": stem
            })

        # Add separator
        if choices:
            choices.append({"value": "---", "label": "--- Individual Analyses ---", "short": "---", "disabled": True})

        # Add individual analyses (from single-analysis files)
        single_files = {stem: analyses[0] for stem, analyses in analyses_by_file.items() if len(analyses) == 1}
        for stem in sorted(single_files.keys()):
            analysis = single_files[stem]
            pipeline = analysis.get("pipeline", "unknown")
            name = analysis.get("name", stem)
            label = f"{stem} ({pipeline})"
            if name != stem:
                label += f" [{name}]"
            choices.append({
                "value": stem,
                "label": label,
                "short": stem
            })

        if has_questionary:
            # Build questionary choices
            q_choices = []
            default_values = []

            for choice in choices:
                if choice.get("disabled"):
                    # Separator
                    q_choices.append(questionary.Separator(choice["label"]))
                else:
                    q_choices.append(questionary.Choice(
                        title=choice["label"],
                        value=choice["value"],
                        shortcut_key=choice.get("shortcut_key")
                    ))
                    # Set production-default as default if available
                    if choice["value"] == "production-default":
                        default_values.append(choice["value"])

            # Add custom option
            q_choices.append(questionary.Choice("Custom (enter manually)", value="custom"))

            checkbox_kwargs = {
                "message": "Select analyses (space to select, enter to continue):",
                "choices": q_choices,
            }
            if default_values:
                checkbox_kwargs["default"] = default_values

            selected_analyses = questionary.checkbox(**checkbox_kwargs).ask()

            # Handle user cancellation (Ctrl+C)
            if selected_analyses is None:
                click.echo("\nSetup cancelled.")
                return

            if "custom" in selected_analyses:
                selected_analyses.remove("custom")
                custom = click.prompt("Enter analysis names (comma-separated)", type=str)
                selected_analyses.extend([a.strip() for a in custom.split(",")])
        else:
            # Simple prompt without questionary
            click.echo("\nAvailable analyses:")

            # Show choices in same order
            choice_list = [c for c in choices if not c.get("disabled") and c["value"] != "custom"]

            for idx, choice in enumerate(choice_list, 1):
                if choice.get("disabled"):
                    click.echo(f"\n{choice['label']}")
                else:
                    # Remove the long description for simpler display
                    short_label = choice["short"]
                    click.echo(f"  {idx}. {short_label}")

            analysis_input = click.prompt(
                "\nSelect analyses (comma-separated numbers or names)",
                type=str,
                default="1" if choice_list else "production-default"
            )

            selected_analyses = []
            for item in analysis_input.split(","):
                item = item.strip()
                if item.isdigit():
                    idx = int(item) - 1
                    if 0 <= idx < len(choice_list):
                        selected_analyses.append(choice_list[idx]["value"])
                else:
                    selected_analyses.append(item)

        # Confirm and execute
        click.echo(click.style("\nSetup Summary", bold=True))
        click.echo("=" * 60)
        click.echo(f"Project: {project_name}")
        click.echo(f"Preset: {preset}")
        click.echo(f"Events: {', '.join(selected_events)} ({len(selected_events)} total)")
        click.echo(f"Analyses: {', '.join(selected_analyses)}")
        click.echo(f"Directory: ./{project_name}")
        click.echo()

        if click.confirm("Proceed with setup?", default=True):
            # Call the setup command (directory defaults to current)
            ctx = click.get_current_context()
            ctx.invoke(
                setup,
                name=project_name,
                preset=preset,
                events=",".join(selected_events),
                analyses=",".join(selected_analyses),
                directory=None,  # Let asimov init handle it in current directory
                dry_run=False,
            )
        else:
            click.echo("Setup cancelled.")

    except Exception as e:
        if not isinstance(e, click.exceptions.Abort):
            click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()


def _get_defaults_for_preset(preset, repo):
    """
    Get the list of default configurations to apply for a preset.

    Returns list of (name, file_path) tuples.
    """
    defaults = []

    if preset == "production":
        # Production preset
        default_files = ["production-pe", "production-pe-priors"]
    else:
        # Testing preset
        default_files = ["testing-pe"]

    for default_name in default_files:
        default_file = repo.get_default(default_name)
        if default_file:
            defaults.append((default_name, default_file))
        else:
            click.echo(
                click.style(f"Warning: Default '{default_name}' not found, skipping", fg="yellow")
            )

    return defaults


def _run_step(description, command, cwd=".", dry_run=False):
    """
    Run a setup step.

    Args:
        description: Human-readable description
        command: Command to run (list of strings)
        cwd: Working directory
        dry_run: If True, just print what would be done
    """
    if dry_run:
        click.echo(f"[DRY RUN] {description}")
        click.echo(f"  Would run: {' '.join(command)} (cwd: {cwd})")
    else:
        click.echo(f"▶ {description}...")
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)

        if result.returncode != 0:
            click.echo(click.style(f"  ✗ Failed: {result.stderr}", fg="red"), err=True)
            raise RuntimeError(f"Command failed: {' '.join(command)}")

        click.echo(click.style(f"  ✓ Done", fg="green"))
