import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import asyncio
import logging, os
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from dotenv import find_dotenv, load_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Define intents with all access
intents = discord.Intents.all()

# Initialize bot
bot = commands.Bot(command_prefix='!', help_command=None, intents=intents)

# Constants
TOKEN = os.environ.get('TOKEN')  # Grabs the bot token from the environment file
CATEGORY_ID = os.environ.get('CATEGORY_ID')  # Grabs the category ID from the environment file
ROLE_ID = os.environ.get('ROLE_ID')  # Grabs the role ID from the environment file
MEMBER_COUNT_CHANNEL_ID = os.environ.get('MEMBER_COUNT_CHANNEL_ID')  # Grabs the member count channel ID from the environment file
BOT_LOG_CHANNEL_ID = os.environ.get('BOT_LOG_CHANNEL_ID')  # Grabs the bot-log channel ID from the environment file
GUILD_ID = os.environ.get('GUILD_ID')  # Grabs the guild ID from the environment file
COMMAND_CHANNEL_ID = os.environ.get('COMMAND_CHANNEL_ID')  # Grabs the command channel ID from the environment file
ACCOUNT_AGE_LIMIT = timedelta(days=int(os.environ.get('ACCOUNT_AGE_LIMIT')))
SPAM_THRESHOLD = int(os.environ.get('SPAM_THRESHOLD'))
SPAM_TIMEOUT = timedelta(minutes=15)
EXCLUDED_CHANNEL_ID = os.environ.get('EXCLUDED_CHANNEL_ID')  # Grabs the excluded channel ID from the environment file
CHANNEL_IDS = {
    "Max Supply:": XXXXXXX,
    "Mined Coins:": XXXXXXXX,
    "Mined Supply:": XXXXXXXX,
    "Nethash:": XXXXXXXX,
    "Blockreward:": XXXXXXXX,
    "Next Reward:": XXXXXXXX,
    "Next Reduction:": XXXXXXXX,
    "Price": XXXXXXXX,
    "mcap": XXXXXXXX,
    "24h Volume:": XXXXXXXX
}

# Variables
user_message_history = defaultdict(lambda: deque(maxlen=SPAM_THRESHOLD))
user_warned = {}

# Status change for some fun little things to be displayed, inside the bot's profile
@tasks.loop(seconds=5)
async def changeStatus():
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.playing, name="with SpectreCoins!"))
    await asyncio.sleep(3)
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="for /help command!"))
    await asyncio.sleep(3)
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.competing, name="Spectre Network!"))
    await asyncio.sleep(3)
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name="active people!"))
    await asyncio.sleep(3)

# Event handlers and commands
@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    changeStatus.start()
    bot.loop.create_task(background_task())
    try:
        synced = await bot.tree.sync()
        logging.info(f"Successfully Synced {len(synced)} commands..")
    except Exception:
        logging.info("Failed to sync commands")
    logging.info("Enabled status updates..")

@bot.event
async def on_member_join(member):
    logging.info(f"Member joined: {member.name} (ID: {member.id})")
    account_age = datetime.now(timezone.utc) - member.created_at
    await log_action(member.guild, f"Member joined: {member.name} (ID: {member.id}), Account age: {account_age}")
    if account_age < ACCOUNT_AGE_LIMIT:
        await handle_suspicious_change(member, "Account age less than 3 days")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    logging.debug(f"Received message from {message.author.name} (ID: {message.author.id}): {message.content}")
    logging.debug(f"Message author's display name: {message.author.display_name}")

    await check_display_name(message.author)
    await check_message_content(message)
    await check_spam(message)

    await bot.process_commands(message)

async def check_display_name(member):
    flagged_keywords = [
        "" # set your keywords here "Word1", "Word2"...
    ]
    if any(keyword.lower() in member.display_name.lower() for keyword in flagged_keywords):
        logging.debug(f"Flagged keyword found in display name: {member.display_name}")
        await handle_suspicious_change(member, "Display name contains flagged keyword")

async def check_message_content(message):
    banned_keywords = [
        "" # set your keywords here "Word1", "Word2"...
    ]
    if any(keyword.lower() in message.content.lower() for keyword in banned_keywords):
        logging.debug(f"Banned keyword found in message: {message.content}")
        await handle_banned_keyword(message)

async def check_spam(message):
    # Exclude the specific channel from spam checks
    if message.channel.id == EXCLUDED_CHANNEL_ID:
        return

    user_history = user_message_history[message.author.id]
    user_history.append(message.content)
    now = datetime.now(timezone.utc)
    if len(user_history) == SPAM_THRESHOLD and all(msg == message.content for msg in user_history):
        if message.author.id not in user_warned or (now - user_warned[message.author.id]) > SPAM_TIMEOUT:
            user_warned[message.author.id] = now
            await message.channel.send(f"{message.author.mention} You have been temporarily muted for 15 minutes due to spamming.")
            logging.info(f"User {message.author} timed out for spamming.")
            user_message_history[message.author.id].clear()
            try:
                await message.author.timeout(SPAM_TIMEOUT, reason="Spamming the same message multiple times in a row.")
            except Exception as e:
                logging.error(f"Failed to timeout user {message.author}: {e}")

async def handle_suspicious_change(member, reason):
    now = datetime.now(timezone.utc)
    account_age = now - member.created_at

    if account_age < ACCOUNT_AGE_LIMIT:
        await send_dm(member, f"You have been kicked from the server due to suspicious activity related to a flagged {reason}.")
        await asyncio.sleep(1)
        await member.kick(reason=reason)
        logging.warning(f"Kicked {member.name} due to {reason} (ID: {member.id})")
        await log_action(member.guild, f"Kicked {member.name} due to {reason} (ID: {member.id})")
    else:
        await send_dm(member, f"You have been banned from the server due to suspicious activity related to a flagged {reason}.")
        await asyncio.sleep(1)
        await member.ban(reason=reason)
        logging.warning(f"Banned {member.name} due to {reason} (ID: {member.id})")
        await log_action(member.guild, f"Banned {member.name} due to {reason} (ID: {member.id})")

    await delete_recent_messages(member.guild, member.id, timedelta(days=7))

async def handle_banned_keyword(message):
    await send_dm(message.author, f"Your message in the server contained banned content and was deleted.")
    await asyncio.sleep(1)
    await message.guild.ban(message.author, reason="Message contained banned content.")
    logging.warning(f"Banned {message.author.name} for sending a message with banned content (ID: {message.author.id})")
    await log_action(message.guild, f"Banned {message.author.name} for sending a message with banned content (ID: {message.author.id})")
    await delete_recent_messages(message.guild, message.author.id, timedelta(days=7))

async def send_dm(user, message):
    try:
        await user.send(message)
    except discord.Forbidden:
        logging.warning(f"Could not send DM to {user.name} (ID: {user.id})")

async def log_action(guild, action):
    log_channel = guild.get_channel(BOT_LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(action)

async def delete_recent_messages(guild, user_id, time_delta):
    after = datetime.now(timezone.utc) - time_delta
    for channel in guild.text_channels:
        async for message in channel.history(after=after):
            if message.author.id == user_id:
                await message.delete()

async def background_task():
    await set_category_name()
    await set_max_supply()
    await update_channels()

async def set_category_name():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if guild:
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        if category:
            await category.edit(name="--Spectre Network Stats--")
            logging.info(f"Category name set to --Spectre Network Stats--")

async def set_max_supply():
    global MAX_SUPPLY
    MAX_SUPPLY = await get_max_supply()
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if guild and MAX_SUPPLY:
        channel_id = CHANNEL_IDS.get("Max Supply:")
        new_name = f"Max Supply: {MAX_SUPPLY / 1e9:.3f} billion"
        await update_or_create_channel(guild, channel_id, "Max Supply:", new_name)

async def get_24h_volume():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.coinpaprika.com/v1/tickers/spr-spectre-network', headers={'accept': 'application/json'}) as response:
            data = await response.json()
            volume_24h = data['quotes']['USD']['volume_24h']
            logging.info(f"24h volume fetched: {volume_24h}")
            return volume_24h

async def update_channels():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if guild:
        while True:
            try:
                await update_channel(guild, "Mined Coins:", get_circulating_supply, calculate_supply_percentage=True)
                await update_channel(guild, "Mined Supply:", get_circulating_supply, supply_percentage=True)
                await update_channel(guild, "Nethash:", get_hashrate, convert_hashrate=True)
                await update_channel(guild, "Blockreward:", get_blockreward)
                await update_channel(guild, "Next Reward:", get_halving_data, next_reward=True)
                await update_channel(guild, "Next Reduction:", get_halving_data, next_reduction=True)
                await update_channel(guild, "Price", get_price_data)
                await update_channel(guild, "mcap", get_market_cap)
                await update_channel(guild, "24h Volume:", get_24h_volume, is_volume=True)
                await update_member_count(guild, ROLE_ID, MEMBER_COUNT_CHANNEL_ID)
            except Exception as e:
                logging.error(f"Error updating channels: {e}")
            await asyncio.sleep(500)

async def update_member_count(guild, role_id, channel_id):
    role = guild.get_role(role_id)
    if role:
        member_count = len(role.members)
        new_name = f"Pi Encryptors: {member_count}"
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.edit(name=new_name)
            logging.info(f"Updated member count channel to {new_name}")

async def update_channel(guild, channel_name, api_call, calculate_supply_percentage=False, supply_percentage=False, next_reward=False, next_reduction=False, convert_hashrate=False, is_volume=False):
    data = await api_call()

    if calculate_supply_percentage or supply_percentage:
        circulating_supply = data
        mined_supply_percentage = (circulating_supply / MAX_SUPPLY) * 100

    if convert_hashrate:
        hashrate = data * 1e6  # Convert to MH/s
        new_name = f"Nethash: {hashrate:.2f} MH/s"
    elif next_reward:
        new_name = f"nReward: {data['nextHalvingAmount']}👇"
    elif next_reduction:
        new_name = f"{data['nextHalvingDate']}"
    elif supply_percentage:
        new_name = f"Mined Supply: {mined_supply_percentage:.2f}%"
    elif channel_name == "Price":
        new_name = f"Price: {data:.5f} USDT"
    elif channel_name == "mcap":
        market_cap = round(data / 1000)
        new_name = f"Mcap: {market_cap}k USDT"
    elif is_volume:
        new_name = f"24h Volume: ${data:.2f}"
    else:
        if channel_name == "Mined Coins:":
            new_name = f"{channel_name} {data / 1e6:.1f} mio"
        elif channel_name == "Blockreward:":
            new_name = f"{channel_name} {data}"
        else:
            if isinstance(data, float):
                new_name = f"{channel_name} {data:.3e}"
            else:
                new_name = f"{channel_name} {data}"

    channel_id = CHANNEL_IDS.get(channel_name)
    await update_or_create_channel(guild, channel_id, channel_name, new_name)

async def update_or_create_channel(guild, channel_id, channel_name, new_name):
    try:
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.edit(name=new_name)
                logging.info(f"Updated channel {channel_name} to {new_name}")
            else:
                new_channel = await guild.create_voice_channel(new_name, category=discord.utils.get(guild.categories, id=CATEGORY_ID))
                CHANNEL_IDS[channel_name] = new_channel.id
                logging.info(f"Created channel {new_name} with ID {new_channel.id}")
        else:
            new_channel = await guild.create_voice_channel(new_name, category=discord.utils.get(guild.categories, id=CATEGORY_ID))
            CHANNEL_IDS[channel_name] = new_channel.id
            logging.info(f"Created channel {new_name} with ID {new_channel.id}")
    except discord.errors.HTTPException as e:
        if e.status == 429:
            retry_after = int(e.response.headers.get('Retry-After', 60))
            logging.warning(f"Rate limited. Retrying in {retry_after} seconds.")
            await asyncio.sleep(retry_after)
            await update_or_create_channel(guild, channel_id, channel_name, new_name)
    except Exception as e:
        logging.error(f"Error creating/updating channel {channel_name}: {e}")

# API functions
async def get_data(url, headers={'accept': 'application/json'}, as_json=True):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json() if as_json else await response.text()
            else:
                logging.error(f"Failed to fetch data from {url}: {response.status}")
                return None

async def get_max_supply():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.spectre-network.org/info/coinsupply/max', headers={'accept': 'text/plain'}) as response:
            max_supply = float(await response.text())
            logging.info(f"Max supply fetched: {max_supply}")
            return max_supply

async def get_circulating_supply():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.spectre-network.org/info/coinsupply/circulating?in_billion=false', headers={'accept': 'text/plain'}) as response:
            circulating_supply = float(await response.text())
            logging.info(f"Circulating supply fetched: {circulating_supply}")
            return circulating_supply

async def get_hashrate():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.spectre-network.org/info/hashrate?stringOnly=false', headers={'accept': 'application/json'}) as response:
            hashrate = (await response.json())['hashrate']
            logging.info(f"Hashrate fetched: {hashrate}")
            return hashrate

async def get_blockreward():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.spectre-network.org/info/blockreward?stringOnly=false', headers={'accept': 'application/json'}) as response:
            blockreward = (await response.json())['blockreward']
            logging.info(f"Blockreward fetched: {blockreward}")
            return blockreward

async def get_halving_data():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.spectre-network.org/info/halving', headers={'accept': 'application/json'}) as response:
            halving_data = await response.json()
            logging.info(f"Halving data fetched: {halving_data}")
            return halving_data

async def get_price_data():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.spectre-network.org/info/price?stringOnly=false', headers={'accept': 'application/json'}) as response:
            last_price = (await response.json())['price']
            logging.info(f"Last price fetched: {last_price}")
            return last_price

async def get_market_cap():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.spectre-network.org/info/marketcap?stringOnly=false', headers={'accept': 'application/json'}) as response:
            market_cap = (await response.json())['marketcap']
            logging.info(f"Market cap fetched: {market_cap}")
            return market_cap

# Define the !calc command
@bot.tree.command(name="calc", description="Calculate rewards based on your hashrate in (Kh/s).")
@app_commands.guild_only()
async def calc(interaction: discord.Interaction, hashrate: float = None):
    if interaction.channel_id != COMMAND_CHANNEL_ID:
        await interaction.response.send_message(f"This command can only be used in the <#1250496462819950667> channel.", ephemeral=True)
        return
    
    if hashrate is None:
        await interaction.response.send_message("Usage: /calc <hashrate_in_kH/s>", ephemeral=True)
        return
    logging.debug(f"Calc command received with hashrate: {hashrate} kH/s")

    blockreward, network_hashrate_ths, spr_price = await fetch_network_info_and_price()
    if blockreward is not None and network_hashrate_ths is not None and spr_price is not None:
        own_hashrate_ths = hashrate / 1_000_000_000  # Convert kH/s to TH/s
        percent_of_network = own_hashrate_ths / float(network_hashrate_ths)
        network_hashrate_mhs = float(network_hashrate_ths) * 1_000_000  # Convert TH/s to MH/s

        blocks_per_day = 86_400  # Number of blocks per day
        total_SPR_per_day = blocks_per_day * blockreward

        reward_message = (f"**Current Network Hashrate:** {network_hashrate_mhs:.2f} MH/s\n"
                          f"**Total Network SPR Mined per Day:** {total_SPR_per_day:.2f} SPR\n"
                          f"**Current Blockreward:** {blockreward} SPR\n"
                          f"**Current Price (USD per SPR):** {spr_price:.4f} USD\n"
                          f"**Your Portion of the Network Hashrate:** ({percent_of_network*100:.3f}%)\n\n"
                          f"**Estimated Mining Rewards:**\n")
        
        rewards = get_mining_rewards(blockreward, percent_of_network)
        for period, reward in rewards.items():
            profit_usd = reward * spr_price
            reward_message += f"- {period}: {reward:.2f} SPR ({profit_usd:.3f} USD)\n"

        await interaction.response.send_message(reward_message)
    else:
        await interaction.response.send_message("Failed to retrieve network information or SPR price. Please try again later.", ephemeral=True)

async def fetch_network_info_and_price():
    try:
        async with aiohttp.ClientSession() as session:
            blockreward_response = await session.get('https://api.spectre-network.org/info/blockreward?stringOnly=false', headers={'accept': 'application/json'})
            blockreward = (await blockreward_response.json()).get('blockreward')

            hashrate_response = await session.get('https://api.spectre-network.org/info/hashrate?stringOnly=false', headers={'accept': 'application/json'})
            network_hashrate = (await hashrate_response.json()).get('hashrate')  # in TH/s

            price_response = await session.get('https://api.spectre-network.org/info/price?stringOnly=false', headers={'accept': 'application/json'})
            spr_price = (await price_response.json()).get('price')  # price in USD

            return blockreward, network_hashrate, spr_price
    except Exception as e:
        logging.error(f"An error occurred while fetching network info or price: {e}")
        return None, None, None

def rewards_in_range(blockreward, blocks):
    return blockreward * blocks

def get_mining_rewards(blockreward, percent_of_network):
    rewards = dict()
    rewards['Hour'] = rewards_in_range(blockreward, 60*60) * percent_of_network
    rewards['Day'] = rewards_in_range(blockreward, 60*60*24) * percent_of_network
    rewards['Week'] = rewards_in_range(blockreward, 60*60*24*7) * percent_of_network
    rewards['Month'] = rewards_in_range(blockreward, 60*60*24*(365.25/12)) * percent_of_network
    rewards['Year'] = rewards_in_range(blockreward, 60*60*24*365.25) * percent_of_network
    return rewards

bot.run(TOKEN)
