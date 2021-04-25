# SERVER COMMANDS

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

restart-server: stop-server start-server

# LIQUIDSOAP 

start-liquidsoap:
	(liquidsoap ~/radio/sunflower.liq > /tmp/sunflower.liquidsoap.log & echo $$! > /tmp/sunflower.liquidsoap.pid)

stop-liquidsoap:
	pkill --pidfile /tmp/sunflower.liquidsoap.pid

restart-liquidsoap: stop-liquidsoap start-liquidsoap

console-liquidsoap:
	telnet localhost 1234

# SCHEDULER

start-scheduler:
	(poetry run python sunflower/scheduler.py & echo $$! > /tmp/sunflower.scheduler.pid)

stop-scheduler:
	pkill --pidfile /tmp/sunflower.scheduler.pid

restart-scheduler: stop-scheduler start-scheduler

# ALIASES

starts: start-server
stops: stop-server
startl: start-liquidsoap
stopl: stop-liquidsoap
restartl: restart-liquidsoap
startr: start-scheduler
stopr: stop-scheduler
restartr: restart-scheduler

# HELP

help:
	@echo "start-server,       starts    Start the API server"
	@echo "stop-server,        stops     Stop the API server"
	@echo "restart-server,     restarts  Restart the API server"
	@echo "start-liquidsoap,   startl    Start Liquidsoap"
	@echo "stop-liquidsoap,    stopl     Stop Liquidsoap"
	@echo "restart-liquidsoap, restartl  Restart Liquidsoap"
	@echo "console-liquidsoap, consolel  Start a telnet session with Liqudsoap"
	@echo "start-scheduler,    startr    Start the radio scheduler"
	@echo "stop-scheduler,     stopr     Stop the radio scheduler"
	@echo "restart-scheduler,  restartr  Restart the radio scheduler"
