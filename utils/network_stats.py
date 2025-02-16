import time
from datetime import datetime

from spectred.SpectredMultiClient import SpectredMultiClient
from utils.deflationary_table import DEFLATIONARY_TABLE
from utils.sompi_to_spr import sompis_to_spr


spectred_hosts = ["127.0.0.1:18110", "mainnet-dnsseed-1.spectre-network.org:18110"]
network_info = {}


async def get_coin_supply(client):
    resp = await client.request("getCoinSupplyRequest", {})
    circulating_sompi = int(resp["getCoinSupplyResponse"]["circulatingSompi"])
    max_sompi = int(resp["getCoinSupplyResponse"]["maxSompi"])
    circulating_spr = sompis_to_spr(circulating_sompi)
    max_spr = sompis_to_spr(max_sompi)

    return {
        "circulatingSupply": circulating_spr,
        "maxSupply": max_spr,
    }


async def get_block_reward(daa_score):
    reward = 0
    for to_break_score in sorted(DEFLATIONARY_TABLE):
        reward = DEFLATIONARY_TABLE[to_break_score]
        if daa_score < to_break_score:
            break
    return reward


async def get_next_block_reward_info(daa_score):
    future_reward = 0
    daa_breakpoint = 0
    daa_list = sorted(DEFLATIONARY_TABLE)

    for i, to_break_score in enumerate(daa_list):
        if daa_score < to_break_score:
            future_reward = DEFLATIONARY_TABLE[daa_list[i + 1]]
            daa_breakpoint = to_break_score
            break

    next_halving_timestamp = int(time.time() + (daa_breakpoint - daa_score))
    next_halving_date = datetime.utcfromtimestamp(next_halving_timestamp).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    days_until_halving = (next_halving_timestamp - int(time.time())) / 86400

    return future_reward, next_halving_timestamp, next_halving_date, days_until_halving


async def get_last_blocks(client, num_blocks=100):
    # get the pruning point
    dag_info_resp = await client.request("getBlockDagInfoRequest", {})
    pruning_point = dag_info_resp["getBlockDagInfoResponse"]["pruningPointHash"]
    print(f"Pruning point hash: {pruning_point}")

    # get selected tip
    selected_tip_resp = await client.request("GetSinkRequest", {})
    selected_tip = selected_tip_resp["GetSinkResponse"]["sink"]
    print(f"Selected tip hash: {selected_tip}")

    block_hashes = []
    low_hash = pruning_point

    while len(block_hashes) < num_blocks:
        # starting from low_hash
        blocks_resp = await client.request(
            "getBlocksRequest",
            {
                "lowHash": low_hash,
                "includeBlocks": True,
                "includeTransactions": False,
            },
        )
        response = blocks_resp["getBlocksResponse"]

        # block hashes and blocks from the response
        blocks_batch = response.get("blocks", [])

        for block in blocks_batch:
            block_hashes.append(block["verboseData"]["hash"])
            if len(block_hashes) >= num_blocks:
                break

        # Update low_hash to the last block's hash for the next iteration
        if block_hashes:
            low_hash = block_hashes[-1]
        else:
            break  # No more blocks to fetch

        # Stop if we've reached the selected tip
        if low_hash == selected_tip:
            break

    return block_hashes


async def get_blocks_detailed(client, start_block_hash):
    resp = await client.request(
        "getBlocksRequest",
        {
            "lowHash": start_block_hash,
            "includeBlocks": True,
            "includeTransactions": True,
        },
    )
    blocks_detailed = resp["getBlocksResponse"]["blocks"]

    return blocks_detailed


async def calculate_tps(client, num_blocks=100):
    block_hashes = await get_last_blocks(client, num_blocks)

    detailed_blocks = await get_blocks_detailed(client, block_hashes[-1])

    tps, sprs = 0, 0
    for block in detailed_blocks:
        tps += len(block["transactions"])
        for tx in block["transactions"]:
            for output in tx["outputs"]:
                sprs += int(output["amount"])

    tps = round(tps / len(detailed_blocks), 1)  # Average TPS over the last 100 blocks
    sprs = round(
        sompis_to_spr(sprs) / len(detailed_blocks), 1
    )  # Average SPR/s over the last 100 blocks

    return tps, sprs


async def update_network_info():
    global network_info

    client = SpectredMultiClient(spectred_hosts)
    await client.initialize_all()

    dag_info_resp = await client.request("getBlockDagInfoRequest", {})
    dag_info = dag_info_resp["getBlockDagInfoResponse"]
    network_name = dag_info["networkName"]
    difficulty = dag_info["difficulty"]
    daa_score = int(dag_info["virtualDaaScore"])

    coin_supply = await get_coin_supply(client)
    block_reward = await get_block_reward(daa_score)
    (
        future_reward,
        next_halving_timestamp,
        next_halving_date,
        days_until_halving,
    ) = await get_next_block_reward_info(daa_score)

    tps, sprs = await calculate_tps(client)

    network_info.update(
        {
            "Network Name": network_name,
            "Max Supply": coin_supply["maxSupply"],
            "Circulating Supply": coin_supply["circulatingSupply"],
            "Difficulty": difficulty,
            "Block Reward": f"{block_reward:.2f} -> {future_reward:.2f} in {days_until_halving:.1f} days",
            "Next Halving Date": f"{next_halving_date} (Timestamp: {next_halving_timestamp})",
            "TPS": f"{tps:.2f}",
            "SPR/s": f"{sprs:.2f}",
        }
    )
