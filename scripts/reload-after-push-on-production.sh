#!/usr/bin/env sh

# This script reloads Sunflower Radio
# It is intended to run on an already-installed environment

# ref="$(cat refs/heads/master)"
echo "[Reload on push] Pycolore remote server."
echo "[Reload on push] "$(python --version)
echo "[Reload on push] Redeploying the scheduler on production branch" # $ref."
# tmpdir="/tmp/radiopycolore/$ref"
# echo "[Reload on push] Cloning into $tmpdir..."
# git clone . "/tmp/radiopycolore/$ref"
echo "[Reload on push] Switching to production branch"
git stash && git checkout production
echo "[Reload on push] Pulling changes"
git pull
# echo "[Reload on push] Adding environment variables..."
# cp /home/git/.radiopycolore_env $tmpdir/.env
# cd "$tmpdir"
echo "[Reload on push] Installing dependencies with Poetry..."
poetry install --no-dev
echo "[Reload on push] Stopping current Sunflower Radio..."
poetry run make stopl
poetry run make stopr
poetry run make stops
echo "[Reload on push] Waiting for Sunflower Radio to stop"
sleep 10
echo "[Reload on push] Restart new version of Sunflower Radio..."
poetry run make startl
poetry run make startr
poetry run make starts
echo "[Reload on push] Finished. See /tmp/sunflower.scheduler.log."
exit 0
