# This file is part of sunflower package. radio
# CLI utils

import click
from click.exceptions import Exit
import subprocess
import os

SERVICE_FILE = """[Unit]
Description=Pycolore Radio generation by liquidsoap

[Service]
Type=simple

User=guillaume
Group=guillaume
UMask=007

ExecStart=/home/guillaume/.opam/4.08.1/bin/liquidsoap /home/guillaume/radio/radio.liq
"""


def abort_cli(msg="Fin du programme."):
    click.secho(msg, fg="red", bold=True)
    raise Exit(1)


def success_cli(msg="Terminé."):
    click.secho(msg, fg="green", bold=True)
    raise Exit(0)


def install_liquidsoap_service():
    click.secho("Creating liquidsoap service.", fg="cyan", bold=True)
    with open("radio.service", "w") as f:
        f.write(SERVICE_FILE)
    install_service = subprocess.Popen(
        ["sudo", "mv", "radio.service", "/etc/systemd/system/radio.service"]
    )
    _, stderr = install_service.communicate()
    if not install_service.returncode:
        success_cli("Service installed. Run start radio command to launch service.")
    click.secho(stderr.decode(), fg="red")
    abort_cli("Operation failed.")


def start_liquidsoap(restart=False):
    """Start liquidsoap as a systemd service. If service doesnt exist, create it."""

    command = "restart" if restart else "start"
    click.secho(
        "Starting liquidsoap service. The following command will be executed.",
        fg="cyan",
        bold=True,
    )
    click.secho("sudo systemctl {} radio".format(command), bold=True)
    rep = click.confirm("Voulez vous continuer ? ")
    if not rep:
        abort_cli("Opération annulée.")
    start_service = subprocess.Popen(
        ["sudo", "systemctl", command, "radio"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = start_service.communicate()
    if not start_service.returncode:
        success_cli("Servide démarré avec succès.")
    if "Failed to {}".format(command) in stderr.decode():
        click.secho(stderr.decode(), fg="red")
        abort_cli(
            "Operation failed. If radio.service is not found, launch install-service command."
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
    click.secho(
        "Stopping liquidsoap service. The following command will be executed.",
        fg="cyan",
        bold=True,
    )
    click.secho("sudo systemctl stop radio", bold=True)
    rep = click.confirm("Voulez vous continuer ? ")
    if not rep:
        abort_cli("Opération annulée.")
    stop_service = subprocess.Popen(
        ["sudo", "systemctl", "stop", "radio"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = stop_service.communicate()
    if not stop_service.returncode:
        success_cli("Servide arrêté avec succès.")
    if "Failed to {}".format("stop") in stderr.decode():
        click.secho(stderr.decode(), fg="red")
        abort_cli("Operation failed.")
