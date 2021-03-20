# uvloop needs to implement shutdown_default_executor()
from uvicorn.workers import UvicornWorker


class SunflowerWorker(UvicornWorker):
    CONFIG_KWARGS = {"loop": "asyncio"}
