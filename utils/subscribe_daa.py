import asyncio
import logging
import time
from collections import deque

import grpc.aio

from spectred.rpc_pb2 import (
    NotifyVirtualDaaScoreChangedRequestMessage,
    RpcNotifyCommand,
)
from spectred.messages_pb2 import SpectredRequest
from spectred.messages_pb2_grpc import RPCStub


# Spectre gRPC Node
SPECTRED_GRPC_HOST = "127.0.0.1:18110"


class BlockProcessor:
    def __init__(self):
        self.bps = {"latest_block_time": None, "avg_block_time": None, "bps": None}
        self.block_times = deque(maxlen=300)
        self.last_block_time = None
        self.last_daa_score = None
        self.block_data = {}

    def calculate_bps(self, block_timestamp: float) -> None:
        block_time = None
        if self.last_block_time:
            block_time = block_timestamp - self.last_block_time
            self.block_times.append(block_time)

        self.last_block_time = block_timestamp

        if len(self.block_times) >= 2:
            avg_block_time = sum(self.block_times) / len(self.block_times)
            bps_value = 1 / avg_block_time if avg_block_time > 0 else 0

            self.bps["latest_block_time"] = block_time
            self.bps["avg_block_time"] = avg_block_time
            self.bps["bps"] = bps_value

            logging.debug(
                f"Block Time: {block_time:.2f} sec | "
                f"Avg Block Time (Last 300): {avg_block_time:.2f} sec | BPS: {bps_value:.2f}"
            )


async def message_iter(queue: asyncio.Queue, lock: asyncio.Semaphore):
    while True:
        message = await queue.get()
        if message is None:
            logging.warning("Received None, stopping message iterator.")
            return
        yield message
        queue.task_done()
        await lock.acquire()


async def subscribe_to_daa():
    processor = BlockProcessor()
    channel = grpc.aio.insecure_channel(SPECTRED_GRPC_HOST)
    await asyncio.wait_for(channel.channel_ready(), timeout=5)
    stub = RPCStub(channel)
    queue = asyncio.Queue()
    concurrency = asyncio.Semaphore(190)

    # Subscribe to Virtual DAA Score Changes
    await queue.put(
        SpectredRequest(
            notifyVirtualDaaScoreChangedRequest=NotifyVirtualDaaScoreChangedRequestMessage(
                command=RpcNotifyCommand.NOTIFY_START
            )
        )
    )

    logging.info("Subscribed to DAA Score updates...")

    async for message in stub.MessageStream(message_iter(queue, concurrency)):
        payload_type = message.WhichOneof("payload")
        message_data = getattr(message, payload_type)

        if payload_type.endswith("Response"):
            concurrency.release()

        if payload_type == "virtualDaaScoreChangedNotification":
            daa_score = message_data.virtualDaaScore
            current_time = time.time()  # Use local time for block timing

            if processor.last_daa_score is None or daa_score > processor.last_daa_score:
                processor.last_daa_score = daa_score
                processor.block_data[daa_score] = {"timestamp": current_time}

                logging.debug(
                    f"New Block Detected! DAA Score: {daa_score}, Local Timestamp: {current_time}"
                )

                processor.calculate_bps(current_time)


if __name__ == "__main__":
    asyncio.run(subscribe_to_daa())
