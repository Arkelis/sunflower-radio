import telnetlib
from contextlib import contextmanager
from logging import Logger
from typing import Optional


@contextmanager
def open_telnet_session(host: str = "localhost", port: int = 1234, logger: Optional[Logger] = None):
    try:
        telnet = telnetlib.Telnet(host, port)
        try:
            yield telnet
        finally:
            telnet.write(b"exit\n")
            telnet.close()
    except ConnectionRefusedError:
        if logger:
            logger.error(f"Could not establish a connection with telnet server {host}:{port}.")
        yield open("/dev/null")
