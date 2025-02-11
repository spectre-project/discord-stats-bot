import time
from datetime import datetime

from spectred.SpectredMultiClient import SpectredMultiClient
from utils.deflationary_table import DEFLATIONARY_TABLE


spectred_hosts = ["127.0.0.1:18110", "mainnet-dnsseed-1.spectre-network.org:18110"]
network_info = {}


async def get_coin_supply(client):
    resp = await client.request("getCoinSupplyRequest", {})
    return {
        "circulatingSupply": resp["getCoinSupplyResponse"]["circulatingSompi"],
        "maxSupply": resp["getCoinSupplyResponse"]["maxSompi"],
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
    blue_score_resp = await client.request("getSinkBlueScoreRequest", {})
    blue_score = blue_score_resp["getSinkBlueScoreResponse"]["blueScore"]

    network_info.update(
        {
            "Network Name": network_name,
            "Max Supply": coin_supply["maxSupply"],
            "Circulating Supply": coin_supply["circulatingSupply"],
            "Difficulty": difficulty,
            "Block Reward": f"{block_reward:.2f} -> {future_reward:.2f} in {days_until_halving:.1f} days",
            "Next Halving Date": f"{next_halving_date} (Timestamp: {next_halving_timestamp})",
            "Last Blue Score": blue_score,
        }
    )
