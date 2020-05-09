import click
from click.exceptions import Exit
from sunflower.utils.cli import (
    start_liquidsoap,
    abort_cli,
    success_cli,
    install_liquidsoap_service,
    start_scheduler,
    stop_scheduler,
    stop_liquidsoap,
)
from sunflower.core.functions import write_liquidsoap_config
from sunflower.channels import tournesol, music


@click.group()
def sunflower():
    """Outil de ligne de commande pour sunflower."""
    click.secho(
        "\nThis is sunflower CLI.\n======================\n", bold=True, fg="blue"
    )


def start_or_restart_component(component, restart=False):
    if component in ("radio", "all"):
        start_liquidsoap(restart)
    if component in ("scheduler", "all"):
        start_scheduler(restart)
    success_cli()


@sunflower.command()
@click.argument("component")
def start(component):
    """Start sunflower component(s). Possible components: scheduler / radio / all (bot)."""
    start_or_restart_component(component)


@sunflower.command()
@click.argument("component")
def restart(component):
    """Restart sunflower component(s). Possible components: scheduler / radio / all (both)."""
    start_or_restart_component(component, restart=True)


@sunflower.command()
@click.argument("component")
def stop(component):
    if component in ("radio", "all"):
        stop_liquidsoap()
    if component in ("scheduler", "all"):
        stop_scheduler()
    success_cli()


@sunflower.command()
def install_service():
    """Install liquidsoap service."""
    install_liquidsoap_service()


@sunflower.command()
@click.option(
    "-o",
    "--filename",
    "--output",
    default="sunflower",
    help="filename without extension",
    show_default=True,
)
def generate_liquidsoap_config(filename):
    """Generate config file for liquidsoap."""
    click.secho("Création du fichier {}.liq...".format(filename), fg="cyan", bold=True)
    try:
        write_liquidsoap_config(music, tournesol, filename=filename)
    except Exception as err:
        abort_cli(err)
    success_cli("Fichier créé")


if __name__ == "__main__":
    sunflower()
