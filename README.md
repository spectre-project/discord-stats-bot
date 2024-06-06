# Spectre Network Discord Stats Bot

This is a Discord bot that fetches and displays real-time statistics from the Spectre Network. It updates the channel names in a specific category with the latest data on max supply, circulating supply, hashrate, block rewards, and halving data. Additionally, it keeps track of the member count for a specified role.

## Features

- Fetches max supply, circulating supply, hashrate, block rewards, and halving data from the Spectre Network.
- Updates Discord voice channel names with the latest statistics.
- Automatically refreshes data every 5 minutes.
- Counts members with a specific role and updates a designated channel with the member count.

## How It Works

The bot fetches data using the REST API provided by the Spectre Network. It makes HTTP GET requests to specific endpoints to retrieve the latest information on max supply, circulating supply, hashrate, block rewards, and halving data. The data is then used to update the names of specified Discord voice channels, providing real-time statistics directly within the Discord server.

For example, the halving data is fetched using the following endpoint:
```
https://api.spectre-network.org/info/halving
```

The bot sends a request to this endpoint, processes the response, and updates the corresponding Discord channel name with the retrieved data.

## Prerequisites

- Python 3.8+
- A Discord bot token
- A Discord server with appropriate permissions

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/spectre-project/SpectreNetworkDiscordStatsBot.git
    cd SpectreNetworkStatsBot
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Configure the bot:
    - Open the `bot.py` file.
    - Replace `'XXXXXX'` with your Discord bot token.
    - Replace the `CATEGORY_ID`, `ROLE_ID`, and `MEMBER_COUNT_CHANNEL_ID` with your actual IDs.

4. Run the bot:
    ```sh
    python bot.py
    ```

## Configuration

- **CATEGORY_NAME:** The name of the category where the bot will update channel names.
- **CATEGORY_ID:** The ID of the category where the bot will operate.
- **ROLE_ID:** The ID of the role whose members are counted.
- **MEMBER_COUNT_CHANNEL_ID:** The ID of the channel where the member count is displayed.

## Usage

Invite the bot to your Discord server and ensure it has permissions to manage channels and read messages in the specified category. The bot will automatically update the specified channels with the latest data from the Spectre Network and the member count for the specified role.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.