import asyncio
import logging
import os
import signal
import socket

from consumer.reader import ConsumerRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def build_consumer_name() -> str:
    # Unique per process, so multiple replicas in the same group don't
    # collide over pending entries.
    return os.environ.get("CONSUMER_NAME", f"{socket.gethostname()}-{os.getpid()}")


async def main() -> None:
    runner = ConsumerRunner(consumer_name=build_consumer_name())

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, runner.request_shutdown)

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
