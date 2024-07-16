# Spectre Network Discord Stats Bot

This is a Discord bot that fetches and displays real-time statistics from the Spectre Network. It updates the channel names in a specific category with the latest data on max supply, circulating supply, hashrate, block rewards, and halving data. Additionally, it keeps track of the member count for a specified role and includes anti-spam features and a mining calculator command.

## Features

- Fetches max supply, circulating supply, hashrate, block rewards, and halving data from the Spectre Network.
- Updates Discord voice channel names with the latest statistics.
- Automatically refreshes data every 5 minutes.
- Counts members with a specific role and updates a designated channel with the member count.
- Anti-spam measures to prevent spam messages.
- Calculator command to estimate mining rewards based on the provided hashrate.

## How It Works

The bot fetches data using the REST API provided by the Spectre Network. It makes HTTP GET requests to specific endpoints to retrieve the latest information on max supply, circulating supply, hashrate, block rewards, and halving data. The data is then used to update the names of specified Discord voice channels, providing real-time statistics directly within the Discord server.

### Detailed Explanation

The bot sends a request to the Spectre Network REST API endpoint to fetch halving data. It processes the response and updates the corresponding Discord channel names with the retrieved data. This process involves the following steps:

1. The API endpoint for fetching halving data is defined as `https://api.spectre-network.org/info/halving`.

2. The bot uses the `aiohttp` library to perform an asynchronous HTTP GET request to the defined endpoint. This allows the bot to fetch data without blocking other operations.

3. The bot processes the JSON response from the API call to extract the necessary halving data. Specifically, it extracts the `nextHalvingAmount` and `nextHalvingDate` fields.

4. Using the extracted data, the bot updates the names of specific Discord voice channels.


## Anti-Spam Measures

The bot includes anti-spam features to prevent users from spamming messages. It tracks message history for each user and issues a timeout if a user sends the same message multiple times in a short period. The bot also monitors display names and message content for flagged keywords and takes appropriate actions such as kicking or banning the user if suspicious activity is detected.

## Calculator Command

The bot includes a calculator command (`!calc`) that allows users to estimate their mining rewards based on their hashrate. Users can enter their hashrate, and the bot will calculate and display the estimated rewards per second, minute, hour, day, week, month, and year.

### Mining Reward Calculation

To estimate the daily coin emissions in a GhostDAG blockchain (with 1 BPS), we can utilize the approximate block time of 1 second. Given that there are 86,400 seconds in a day (24 hours * 60 minutes * 60 seconds), we can calculate the total number of blocks mined per day.

Once we know the daily block emissions, we can estimate our share of the network's mining rewards.

For example:
- If the network hash rate (nethash) is 100 KH/s and your miner's hash rate is 10 KH/s, then your miner contributes 10% to the total network hash rate.
- Consequently, you would receive 10% of the blocks mined daily.
- Let's say that emissions are 100,000 SPR per day, your network share is 10%, so 100,000 SPR × 0.1 (10%) = 10,000 SPR per 24 hours.

The calculator retrieves blockchain data such as the network hash rate (nethash) and current block reward from the Spectre REST API to perform these calculations.

Keep in mind that this calculation is an estimate. Your actual block rewards can vary due to factors such as luck, network latency, and other conditions. This script provides a basic estimation of potential earnings.

## Prerequisites

- Python 3.8+
- A Discord bot token
- A Discord server with appropriate permissions

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/spectre-project/discord-stats-bot.git
    cd discord-stats-bot
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Configure the bot:
    - Rename the ``example.env`` to ``.env``.
    - Open ``.env`` file with any text editor.
    ```
    TOKEN= # Bot Token
    ```
    - Fill in your bot token next to the ``=`` sign in the first line.
    - Fill in the `CHANNEL_ID` with your actual IDs.

4. Run the bot:
    ```sh
    python bot.py
    ```

## Usage

Invite the bot to your Discord server and ensure it has permissions to manage channels and read messages in the specified category. The bot will automatically update the specified channels with the latest data from the Spectre Network and the member count for the specified role. Use the `!calc <hashrate_in_kH/s>` command to estimate mining rewards based on your hashrate.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Development Fund

The devfund is a fund managed by the Spectre community in order to fund Spectre development. Please consider a donation to support ongoing and future projects.

```
spectre:qrxf48dgrdkjxllxczek3uweuldtan9nanzjsavk0ak9ynwn0zsayjjh7upez
```

## License

This project is licensed under the MIT License.
