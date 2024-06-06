import discord
import requests
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define intents with member access
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True  # Enable access to member information

client = discord.Client(intents=intents)

TOKEN = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'  # Replace with your actual token

CATEGORY_NAME = "--Spectre Network Stats--"
CATEGORY_ID = 1236812312921509959  # Replace with your actual category ID
ROLE_ID = 1233113243741061241  # Replace with your actual role ID
MEMBER_COUNT_CHANNEL_ID = 1248376416098189475  # Replace with your actual channel ID

# Variable to store max supply
MAX_SUPPLY = None

# Function to get max supply
async def get_max_supply():
    response = requests.get('https://api.spectre-network.org/info/coinsupply/max', headers={'accept': 'text/plain'})
    max_supply = float(response.text)
    logging.info(f"Max supply fetched: {max_supply}")
    return max_supply

# Function to get circulating supply
async def get_circulating_supply():
    response = requests.get('https://api.spectre-network.org/info/coinsupply/circulating?in_billion=false', headers={'accept': 'text/plain'})
    circulating_supply = float(response.text)
    logging.info(f"Circulating supply fetched: {circulating_supply}")
    return circulating_supply

# Function to get hashrate
async def get_hashrate():
    response = requests.get('https://api.spectre-network.org/info/hashrate?stringOnly=false', headers={'accept': 'application/json'})
    hashrate = response.json()['hashrate']
    logging.info(f"Hashrate fetched: {hashrate}")
    return hashrate

# Function to get blockreward
async def get_blockreward():
    response = requests.get('https://api.spectre-network.org/info/blockreward?stringOnly=false', headers={'accept': 'application/json'})
    blockreward = response.json()['blockreward']
    logging.info(f"Blockreward fetched: {blockreward}")
    return blockreward

# Function to get halving data
async def get_halving_data():
    response = requests.get('https://api.spectre-network.org/info/halving', headers={'accept': 'application/json'})
    halving_data = response.json()
    logging.info(f"Halving data fetched: {halving_data}")
    return halving_data

# Predefined channel IDs (replace with your actual IDs)
CHANNEL_IDS = {
    "Max Supply:": 1248301536887705750,
    "Mined Coins:": 1248371053902958707,
    "Mined Supply:": 1248371154616455199,
    "Nethash:": 1248371213483376812,
    "Blockreward:": 1248371229640102050,
    "Next Reward:": 1248371333092343971,
    "Next Reduction:": 1248371393285062807
}

async def set_category_name():
    await client.wait_until_ready()
    guild = discord.utils.get(client.guilds, name="Spectre Network")
    
    if guild:
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        if category:
            await category.edit(name=CATEGORY_NAME)
            logging.info(f"Category name set to {CATEGORY_NAME}")
        else:
            logging.info(f"Category with ID {CATEGORY_ID} not found")

async def set_max_supply():
    global MAX_SUPPLY
    MAX_SUPPLY = await get_max_supply()
    await client.wait_until_ready()
    guild = discord.utils.get(client.guilds, name="Spectre Network")
    
    if guild:
        channel_id = CHANNEL_IDS.get("Max Supply:")
        new_name = f"Max Supply: {MAX_SUPPLY / 1e9:.3f} billion"
        await update_or_create_channel(guild, channel_id, "Max Supply:", new_name)

async def update_channels():
    await client.wait_until_ready()
    guild = discord.utils.get(client.guilds, name="Spectre Network")
    
    if guild:
        while True:
            await update_channel(guild, "Mined Coins:", get_circulating_supply, True)
            await update_channel(guild, "Mined Supply:", get_circulating_supply, True, True)
            await update_channel(guild, "Nethash:", get_hashrate, convert_hashrate=True)
            await update_channel(guild, "Blockreward:", get_blockreward)
            await update_channel(guild, "Next Reward:", get_halving_data, next_reward=True)
            await update_channel(guild, "Next Reduction:", get_halving_data, next_reduction=True)
            await update_member_count(guild, ROLE_ID, MEMBER_COUNT_CHANNEL_ID)
            await asyncio.sleep(300)  # Cooldown after updating all channels

async def update_member_count(guild, role_id, channel_id):
    role = guild.get_role(role_id)
    if role:
        member_count = len(role.members)
        new_name = f"Pi Encryptors: {member_count}"
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.edit(name=new_name)
            logging.info(f"Updated member count channel to {new_name}")
        else:
            logging.warning(f"Channel with ID {channel_id} not found")

async def update_channel(guild, channel_name, api_call, calculate_supply_percentage=False, supply_percentage=False, next_reward=False, next_reduction=False, convert_hashrate=False):
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
    else:
        if channel_name == "Mined Coins:":
            new_name = f"{channel_name} {round(data / 1e6)} mio"
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

async def background_task():
    await set_category_name()
    await set_max_supply()
    await update_channels()

@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}')
    client.loop.create_task(background_task())

client.run(TOKEN)