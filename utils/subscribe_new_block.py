import os
from dotenv import load_dotenv
import asyncio
import logging
from collections import deque

from utils.sompi_to_spr import sompis_to_spr
from spectred.SpectredMultiClient import SpectredMultiClient


load_dotenv()
SPECTRED_HOSTS = os.getenv("SPECTRED_HOSTS").split(",")


class BlockProcessor:
    def __init__(self):
        self.block_times = deque(maxlen=30)
        self.blocks_cache = deque(maxlen=100)
        self.sorted_blocks = []
        self.bps = {
            "latest_block_time": None,
            "avg_block_time": None,
            "bps": None,
        }
        self.tps_sprs = {
            "tps": None,
            "sprs": None,
        }

    def calculate_bps(self, block_timestamp: int) -> None:
        block_timestamp /= 1000
        self.sorted_blocks.append(block_timestamp)

        # descending order and keep only latest 30 blocks
        self.sorted_blocks.sort(reverse=True)
        self.sorted_blocks = self.sorted_blocks[:30]

        if len(self.sorted_blocks) >= 30:
            # start after we have >= 30 blocks
            self.block_times = [
                self.sorted_blocks[i - 1] - self.sorted_blocks[i]
                for i in range(1, len(self.sorted_blocks))
            ]

            if len(self.block_times) >= 2:
                avg_block_time = sum(self.block_times) / len(self.block_times)
                bps_value = 1 / avg_block_time if avg_block_time > 0 else 0

                self.bps["latest_block_time"] = self.block_times[-1]
                self.bps["avg_block_time"] = avg_block_time
                self.bps["bps"] = bps_value

                logging.debug(
                    f"Block Time: {self.block_times[-1]:.2f} sec | "
                    f"Avg Block Time (Last {len(self.block_times)}): {avg_block_time:.2f} sec | BPS: {bps_value:.2f}"
                )

    def calculate_tps_spr_s(self) -> None:
        if len(self.blocks_cache) < 30:
            return

        total_txs = 0
        total_sprs = 0

        for block in self.blocks_cache:
            total_txs += block["txCount"]

            for tx in block["txs"]:
                for _, amount in tx["outputs"]:
                    total_sprs += int(amount)

        average_tps = round(total_txs / len(self.blocks_cache), 1)
        average_sprs = round(sompis_to_spr(total_sprs) / len(self.blocks_cache), 1)

        self.tps_sprs["tps"] = average_tps
        self.tps_sprs["sprs"] = average_sprs

        logging.debug(f"TPS: {average_tps} | SPR/s: {average_sprs}")

    def add_block_to_cache(self, block_info) -> None:
        block_data = {
            "block_hash": block_info["verboseData"]["hash"],
            "difficulty": block_info["verboseData"]["difficulty"],
            "blueScore": block_info["header"]["blueScore"],
            "timestamp": block_info["header"]["timestamp"],
            "txCount": len(block_info["transactions"]),
            "txs": [
                {
                    "txId": tx["verboseData"]["transactionId"],
                    "outputs": [
                        (
                            output["verboseData"]["scriptPublicKeyAddress"],
                            output["amount"],
                        )
                        for output in tx["outputs"]
                    ],
                }
                for tx in block_info["transactions"]
            ],
        }

        self.blocks_cache.append(block_data)
        logging.debug(f"Added block to cache: {block_data}")


async def subscribe_block_added(processor: BlockProcessor):
    spectred_client = SpectredMultiClient(SPECTRED_HOSTS)
    await spectred_client.initialize_all()

    async def on_new_block(event):
        try:
            if "blockAddedNotification" not in event:
                logging.debug(f"Ignoring non-block event: {event}")
                return

            block_info = event["blockAddedNotification"]["block"]
            processor.add_block_to_cache(block_info)
            timestamp = block_info["header"]["timestamp"]
            processor.calculate_bps(float(timestamp))
            processor.calculate_tps_spr_s()

            logging.debug(f"New Block! {block_info['verboseData']['hash']}")
        except Exception as e:
            logging.error(f"error processing block: {e}")

    await spectred_client.notify("notifyBlockAddedRequest", None, on_new_block)


if __name__ == "__main__":
    processor = BlockProcessor()
    asyncio.run(subscribe_block_added(processor))
