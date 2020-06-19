# This file is part of sunflower package. radio
# CLI utils

import click
from click.exceptions import Exit
import subprocess
import os

try:
    from sunflower.settings import LIQUIDSOAP_SERVICE
except ImportError:
    LIQUIDSOAP_SERVICE = "radio"


def abort_cli(msg="Fin du programme."):
    click.secho(msg, fg="red", bold=True)
    raise Exit(1)


def success_cli(msg="Terminé."):
    click.secho(msg, fg="green", bold=True)


def start_liquidsoap(restart=False):
    """Start liquidsoap as a systemd service. If service doesnt exist, create it."""

    service_name = LIQUIDSOAP_SERVICE
    command = "restart" if restart else "start"
    click.secho(
        "Starting liquidsoap service. The following command will be executed.",
        fg="cyan",
        bold=True,
    )
    click.secho(f"sudo systemctl {command} {service_name}", bold=True)
    rep = click.confirm("Voulez vous continuer ? ")
    if not rep:
        abort_cli("Opération annulée.")
    start_service = subprocess.Popen(
        ["sudo", "systemctl", command, service_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = start_service.communicate()
    if not start_service.returncode:
        success_cli("Servide démarré avec succès.")
    if "Failed to {}".format(command) in stderr.decode():
        click.secho(stderr.decode(), fg="red")
        abort_cli(
            "Operation failed. If radio.service is not found, create it."
        )


def start_scheduler(restart=False):
    if restart:
        stop_scheduler()
    click.secho("Starting scheduler", bold=True, fg="cyan")
    os.system("python sunflower/scheduler.py")
    success_cli("Scheduler started.")


def stop_scheduler():
    click.secho("Killing current scheduler", bold=True, fg="cyan")
    os.system("kill $(cat /tmp/sunflower-radio-scheduler.pid)")


def stop_liquidsoap():
    service_name = LIQUIDSOAP_SERVICE
    click.secho(
        "Stopping liquidsoap service. The following command will be executed.",
        fg="cyan",
        bold=True,
    )
    click.secho(f"sudo systemctl stop {service_name}", bold=True)
    rep = click.confirm("Voulez vous continuer ? ")
    if not rep:
        abort_cli("Opération annulée.")
    stop_service = subprocess.Popen(
        ["sudo", "systemctl", "stop", service_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = stop_service.communicate()
    if not stop_service.returncode:
        success_cli("Servide arrêté avec succès.")
    if "Failed to {}".format("stop") in stderr.decode():
        click.secho(stderr.decode(), fg="red")
        abort_cli("Operation failed.")
