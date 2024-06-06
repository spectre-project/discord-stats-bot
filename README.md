# Spectre Network Stats Bot

This is a Discord bot that fetches and displays real-time statistics from the Spectre Network. It updates the channel names in a specific category with the latest data on max supply, circulating supply, hashrate, block rewards, and halving data. Additionally, it keeps track of the member count for a specified role.

## Features

- Fetches max supply, circulating supply, hashrate, block rewards, and halving data from the Spectre Network.
- Updates Discord voice channel names with the latest statistics.
- Automatically refreshes data every 5 minutes.
- Counts members with a specific role and updates a designated channel with the member count.

## Prerequisites

- Python 3.8+
- A Discord bot token
- A Discord server with appropriate permissions

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/SpectreNetworkStatsBot.git
    cd SpectreNetworkStatsBot
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Configure the bot:
    - Open the `bot.py` file.
    - Replace `'XXXXXXXX'` with your Discord bot token.
    - Replace the `CATEGORY_ID` and `CHANNEL_IDS` with your actual category and channel IDs.

4. Run the bot:
    ```sh
    python bot.py
    ```

## Configuration

- **CATEGORY_NAME:** The name of the category where the bot will update channel names.
- **CATEGORY_ID:** The ID of the category where the bot will operate.
- **CHANNEL_IDS:** A dictionary mapping statistic names to channel IDs.

## Usage

Invite the bot to your Discord server and ensure it has permissions to manage channels and read messages in the specified category. The bot will automatically update the specified channels with the latest data from the Spectre Network.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.

---

### `requirements.txt`
```plaintext
discord.py
requests
```

Feel free to adjust the repository URL and any specific details based on your setup and preferences.