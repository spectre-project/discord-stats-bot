import logging

import discord
from discord import app_commands

from utils.network_stats import update_network_info, network_info
from utils.get_price_data import get_spr_price


async def get_net_info():
    await update_network_info()
    try:
        logging.debug(f"Network info: {network_info}")
        diff = float(network_info["Difficulty"])
        current_reward = float(network_info["Block Reward"].split(" -> ")[0])
        net_hash_mhs = (diff * 2) / 1e6
        return current_reward, net_hash_mhs
    except Exception as err:
        logging.error(f"Error fetching network info: {err}")
        return None, None


def calc_rewards(reward, share):
    return {
        "Hour": reward * 3600 * share,
        "Day": reward * 86400 * share,
        "Week": reward * 86400 * 7 * share,
        "Month": reward * 86400 * (365.25 / 12) * share,
        "Year": reward * 86400 * 365.25 * share,
    }


@app_commands.command(
    name="calc", description="Estimate mining rewards from your hashrate."
)
@app_commands.describe(hashrate="Your mining hashrate in kH/s")
async def calc(interaction: discord.Interaction, hashrate: float):
    await interaction.response.defer()

    if hashrate <= 0:
        await interaction.followup.send("Please provide a valid hashrate >0")
        return

    current_reward, net_hash_mhs = await get_net_info()
    spr_price = await get_spr_price()

    if current_reward is None or net_hash_mhs is None:
        await interaction.followup.send(
            "Error fetching network data. Please try again later."
        )
        return

    user_hash_mhs = hashrate / 1e3  # kH/s to MH/s
    share = user_hash_mhs / net_hash_mhs

    rewards = calc_rewards(current_reward, share)
    daily_mined = current_reward * 86400
    emissions = daily_mined * spr_price

    response = (
        f"**Network Hashrate:** {net_hash_mhs:.2f} MH/s\n"
        f"**Daily SPR Mined:** {daily_mined:.1f} SPR\n"
        f"**24h Emissions:** {emissions:.2f} $\n"
        f"**Block Reward:** {current_reward:.2f} SPR\n"
        f"**SPR Price:** ${spr_price:.5f} USD\n"
        f"**Your Network Share:** {share * 100:.3f}%\n\n"
        f"**Estimated Earnings:**\n"
        f"**Hourly:** {rewards['Hour']:.2f} SPR (${rewards['Hour'] * spr_price:.3f} USD)\n"
        f"**Daily:** {rewards['Day']:.2f} SPR (${rewards['Day'] * spr_price:.3f} USD)\n"
        f"**Weekly:** {rewards['Week']:.2f} SPR (${rewards['Week'] * spr_price:.3f} USD)\n"
        f"**Monthly:** {rewards['Month']:.2f} SPR (${rewards['Month'] * spr_price:.3f} USD)\n"
        f"**Yearly:** {rewards['Year']:.2f} SPR (${rewards['Year'] * spr_price:.3f} USD)"
    )

    await interaction.followup.send(response)


def setup(bot: discord.Client):
    bot.tree.add_command(calc)
