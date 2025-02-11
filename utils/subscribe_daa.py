import asyncio
import logging
import time
from collections import deque

import grpc.aio

from spectred.rpc_pb2 import (
    GetBlockDagInfoRequestMessage,
    NotifyNewBlockTemplateRequestMessage,
)
from spectred.messages_pb2 import SpectredRequest
from spectred.messages_pb2_grpc import RPCStub


# Spectre gRPC Node
SPECTRED_GRPC_HOST = "127.0.0.1:18110"

# Store timestamps, block times, and BPS
bps = {"latest_block_time": None, "avg_block_time": None, "bps": None}
last_block_time = None
block_times = deque(maxlen=300)  # Store only last 300 blocks


async def message_iter(queue: asyncio.Queue, lock: asyncio.Semaphore):
    message = await queue.get()
    while message is not None:
        yield message
        queue.task_done()
        await lock.acquire()
        message = await queue.get()
    queue.task_done()


async def subscribe_to_daa():
    global last_block_time, block_times, bps

    channel = grpc.aio.insecure_channel(SPECTRED_GRPC_HOST)
    await asyncio.wait_for(channel.channel_ready(), timeout=2)

    stub = RPCStub(channel)
    queue = asyncio.Queue()

    # Subscribe
    await queue.put(
        SpectredRequest(getBlockDagInfoRequest=GetBlockDagInfoRequestMessage())
    )
    await queue.put(
        SpectredRequest(
            notifyNewBlockTemplateRequest=NotifyNewBlockTemplateRequestMessage()
        )
    )

    concurrency = asyncio.Semaphore(190)

    async for message in stub.MessageStream(message_iter(queue, concurrency)):
        payload_type = message.WhichOneof("payload")
        message_data = getattr(message, payload_type)

        if payload_type.endswith("Response"):
            concurrency.release()

        # DAA Change
        if payload_type == "getBlockDagInfoResponse":
            blue_score = (
                message_data.virtualParentHashes[0]
                if message_data.virtualParentHashes
                else "N/A"
            )
            logging.debug(f"Blue Score Updated: {blue_score}")

        elif payload_type == "newBlockTemplateNotification":
            current_time = time.time()
            block_time = None

            if last_block_time:
                block_time = current_time - last_block_time  # time difference
                block_times.append(block_time)  # store latest block time

            last_block_time = current_time  # Update last block time

            # average of last 300 blocks (if at least 2 blocks exist)
            if len(block_times) >= 2:
                avg_block_time = sum(block_times) / len(block_times)
                bps_value = 1 / avg_block_time if avg_block_time > 0 else 0

                bps["latest_block_time"] = block_time
                bps["avg_block_time"] = avg_block_time
                bps["bps"] = bps_value

                logging.debug(
                    f"New block detected! Block Time: {block_time:.2f} sec | Avg Block Time (Last 300): {avg_block_time:.2f} sec | BPS: {bps_value:.2f}"
                )
            else:
                logging.debug(
                    f"New block detected! Block Time: {block_time:.2f} sec (Not enough data for avg)"
                    if block_time is not None
                    else "New block detected! First block, waiting for more data."
                )

            await queue.put(
                SpectredRequest(getBlockDagInfoRequest=GetBlockDagInfoRequestMessage())
            )


if __name__ == "__main__":
    asyncio.run(subscribe_to_daa())
