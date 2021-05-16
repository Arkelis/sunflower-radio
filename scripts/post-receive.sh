#!/usr/bin/env sh
# to place on bare repo on prod server for reloading on push

export PATH="/home/git/.pyenv/versions/3.8.9/bin/:$PATH"
export PATH="/home/git/.poetry/bin:$PATH"
ref="$(cat refs/heads/master)"
echo "[Reload on push] Pycolore remote server."
echo "[Reload on push] "$(python --version)
echo "[Reload on push] Redeploying the scheduler on commit $ref."
tmpdir="/tmp/radiopycolore/$ref"
echo "[Reload on push] Cloning into $tmpdir..."
git clone . "/tmp/radiopycolore/$ref"
echo "[Reload on push] Adding environment variables..."
cp /home/git/.radiopycolore_env $tmpdir/.env
cd "$tmpdir"
echo "[Reload on push] Installing dependencies with Poetry..."
poetry install --no-dev
echo "[Reload on push] Restarting scheduler..."
make stop-scheduler
make start-scheduler
echo "[Reload on push] Finished. See /tmp/sunflower.scheduler.log."
