#!/usr/bin/env python3

"""This script reloads Sunflower Radio

It is intended to run on an already-installed environment
"""

import contextlib
import os
import signal
import subprocess
import sys
import time


# ref="$(cat refs/heads/master)"
print("[Reload on push] Pycolore remote server.")
print(f"[Reload on push] {sys.version}")
print("[Reload on push] Redeploying the scheduler on production branch") # $ref."

# tmpdir="/tmp/radiopycolore/$ref"
# print("[Reload on push] Cloning into $tmpdir..."
# git clone . "/tmp/radiopycolore/$ref"
print("[Reload on push] Switching to production branch")
subprocess.run(["git", "stash"])
subprocess.run(["git", "checkout", "production"])
print("[Reload on push] Pulling changes")
subprocess.run(["git", "pull"])

# print("[Reload on push] Adding environment variables..."
# cp /home/git/.radiopycolore_env $tmpdir/.env
# cd "$tmpdir"
print("[Reload on push] Installing dependencies with Poetry...")
subprocess.run(["poetry", "install", "--no-dev"])

print("[Reload on push] Stopping current Sunflower Radio...")
with contextlib.suppress(FileNotFoundError, ProcessLookupError):
    with open("/tmp/sunflower.liquidsoap.pid") as f:
        os.kill(int(f.read()), signal.SIGTERM)
    with open("/tmp/sunflower.scheduler.pid") as f:
        os.kill(int(f.read()), signal.SIGTERM)
    with open("/tmp/sunflower.server.pid") as f:
        os.kill(int(f.read()), signal.SIGTERM)

print("[Reload on push] Waiting for Sunflower Radio to stop")
time.sleep(10)

print("[Reload on push] Restart new version of Sunflower Radio...")
subprocess.run(["poetry", "run",
    "gunicorn", "-w", "2", "-k", "sunflower.core.worker.SunflowerWorker",
    "--bind", "unix:/tmp/sunflower.gunicorn.sock",
    "--daemon",
    "--pid", "/tmp/sunflower.server.pid",
    "--access-logfile", "/tmp/sunflower.access.log",
    "--error-logfile", "/tmp/sunflower.error.log",
    "--forwarded-allow-ips", "*",
    "--capture-output",
    "server.server:app"])
with open("/tmp/sunflower.liquidsoap.pid", "w") as f:
    pid = subprocess.Popen(["liquidsoap", f"{os.environ['HOME']}/radio/sunflower.liq"], start_new_session=True).pid
    f.write(f"{pid}\n")
with open("/tmp/sunflower.scheduler.pid", "w") as f:
    pid = subprocess.Popen(["poetry", "run", "python", "sunflower/scheduler.py"], start_new_session=True).pid
    f.write(f"{pid}\n")

print("[Reload on push] Finished. See /tmp/sunflower.scheduler.log.")
