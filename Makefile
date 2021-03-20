start-server:
	poetry run gunicorn -w 2 -k sunflower.core.worker.SunflowerWorker \
		--bind unix:/tmp/sunflower.gunicorn.sock \
		--daemon \
		--access-logfile /tmp/sunflower.access.log \
		--error-logfile /tmp/sunflower.error.log \
		server.server:app
	@echo "Logs and socket are in /tmp"

stop-server:
	pkill gunicorn

start-liquidsoap:
	(liquidsoap ~/radio/sunflower.liq > /tmp/sunflower.liquidsoap.log & echo $$! > /tmp/sunflower.liquidsoap.pid)

stop-liquidsoap:
	pkill --pidfile /tmp/sunflower.liquidsoap.pid

start-scheduler:
	(poetry run python sunflower/scheduler.py & echo $$! > /tmp/sunflower.scheduler.pid)

stop-scheduler:
	pkill --pidfile /tmp/sunflower.scheduler.pid

restart-liquidsoap: stop-liquidsoap start-liquidsoap

restart-scheduler: stop-scheduler start-scheduler

restartr: restart-scheduler
restartl: restart-liquidsoap

help:
	@echo "start-server,       starts    Start the API server"
	@echo "stop-server,        stops     Stop the API server"
	@echo "restart-server,     restarts  Restart the API server"
	@echo "start-liquidsoap,   startl    Start Liquidsoap"
	@echo "stop-liquidsoap,    stopl     Stop Liquidsoap"
	@echo "restart-liquidsoap, restartl  Restart Liquidsoap"
	@echo "start-scheduler,    startr    Start the radio scheduler"
	@echo "stop-scheduler,     stopr     Stop the radio scheduler"
	@echo "restart-scheduler,  restartr  Restart the radio scheduler"
