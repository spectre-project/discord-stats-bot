import os
import logging
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

from commands.calculate import setup as setup_calculate
from utils.spam import setup as setup_spam
from utils.network_stats import update_network_info, network_info
from utils.get_price_data import get_spr_price, get_spr_volume
from utils.subscribe_daa import subscribe_to_daa, BlockProcessor


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

CHANNEL_IDS = {
    "Price": int(os.getenv("CHANNEL_PRICE")),
    "24h_Volume": int(os.getenv("CHANNEL_TRADING_VOLUME")),
    "mcap": int(os.getenv("CHANNEL_MCAP")),
    "Max Supply": int(os.getenv("CHANNEL_MAX_SUPPLY")),
    "Mined Coins": int(os.getenv("CHANNEL_MINED_COINS")),
    "Mined Supply": int(os.getenv("CHANNEL_MINED_SUPPLY")),
    "Nethash": int(os.getenv("CHANNEL_NETHASH")),
    "Blockreward": int(os.getenv("CHANNEL_BLOCKREWARD")),
    "TPS_SPR_S": int(os.getenv("CHANNEL_TPS_SPR_S")),
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="/", intents=intents)

previous_updates = {}
processor = BlockProcessor()


async def update_discord_channels():
    global previous_updates
    await bot.wait_until_ready()

    first_run = True

    while True:
        logging.debug("Fetching network data...")
        await update_network_info()
        spr_price = await get_spr_price()
        spr_volume = await get_spr_volume()
        logging.debug(f"Fetched SPR Market Data: {spr_price} - {spr_volume}")

        if network_info:
            try:
                logging.debug(f"network_info: {network_info}")
                logging.debug(f"BlockProcessor class: {BlockProcessor}")

                circulating_supply = float(network_info["Circulating Supply"])
                max_supply = float(network_info["Max Supply"])
                difficulty = float(network_info["Difficulty"])
                block_reward_text = network_info["Block Reward"]
                hashrate = (difficulty * 2) / 1e6

                market_cap = spr_price * circulating_supply
                mined_supply = (circulating_supply / max_supply) * 100

                tps = network_info["TPS"]
                sprs = network_info["SPR/s"]

                updates = {
                    "Price": f"💲: ${spr_price:.5f}",
                    "24h_Volume": f"📊: ${spr_volume:.1f}",
                    "mcap": f"mcap: ${market_cap:,.1f}",
                    "Max Supply": f"Max: {max_supply:,.0f} SPR",
                    "Mined Coins": f"⛏️: {circulating_supply:,.0f} SPR",
                    "Mined Supply": f"⛏️: {mined_supply:.3f}% Mined",
                    "Nethash": f"⚡ {hashrate:.3f} MH/s",
                    "Blockreward": f"{block_reward_text}",
                    "TPS": f"TPS: {tps} ┃ ({sprs} SPR/s)",
                }

                # update channels only if changed
                logging.debug("Checking for changes...")
                for key, channel_id in CHANNEL_IDS.items():
                    if key in updates:
                        if (
                            key not in previous_updates
                            or previous_updates[key] != updates[key]
                        ):
                            logging.info(
                                f"Value change detected for {key}: {previous_updates.get(key, 'None')} -> {updates[key]}"
                            )
                            channel = bot.get_channel(channel_id)
                            if not channel:
                                logging.error(
                                    f"Channel {key} ({channel_id}) not found!"
                                )
                                continue
                            logging.info(f"Updating {key} channel to: {updates[key]}")
                            await channel.edit(name=updates[key])
                            previous_updates[key] = updates[key]
                            await asyncio.sleep(30)

                # update bot display name with BPS or default name
                if processor.bps["bps"] is not None:
                    new_bot_name = (
                        f"BPS: {processor.bps['bps']:.2f}"  # Format BPS value
                    )
                else:
                    new_bot_name = "Spectre Bot"  # Default name

                logging.info(f"Updating bot display name to: {new_bot_name}")
                guild = bot.get_guild(GUILD_ID)
                if guild:
                    await guild.me.edit(nick=new_bot_name)
                else:
                    logging.error("Guild not found, cannot update bot name.")
                await asyncio.sleep(5)  # Short delay to avoid rate limits

                # update Discord activity status with latest DAA Score
                latest_daa_score = processor.last_daa_score
                logging.debug(f"Received DAA score: {latest_daa_score}")
                if latest_daa_score is not None:
                    activity_text = f"DAA Score: {latest_daa_score}"
                else:
                    activity_text = "Use /calc to estimate rewards"  # default activity

                logging.info(f"Updating bot activity to: {activity_text}")
                status = discord.Activity(
                    type=discord.ActivityType.watching,
                    name=activity_text,
                )
                await bot.change_presence(status=discord.Status.online, activity=status)
                await asyncio.sleep(5)  # avoid rate limits

            except Exception as e:
                logging.error(f"Error updating Discord channels: {e}")

        # Skip the sleep on the first run
        if first_run:
            first_run = False
        else:
            logging.info("Sleeping for 5min before next update...")
            await asyncio.sleep(600)


@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    setup_calculate(bot)
    setup_spam(bot)
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    logging.info("commands synced successfully!")

    asyncio.create_task(subscribe_to_daa(processor))
    asyncio.create_task(update_discord_channels())


if __name__ == "__main__":
    logging.info("Starting bot...")
    bot.run(TOKEN)
