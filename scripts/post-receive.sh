# to place on bare repo on prod server for reloading on push

ref="$(cat refs/head/master)"
tmpdir="/tmp/radiopycolore/$ref"
git clone . "/tmp/radiopycolore/$(cat refs/head/devel)"
cd "$tmpdir"
poetry install
make restart-scheduler
