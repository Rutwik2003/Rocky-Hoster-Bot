# Discord Minecraft Server Bot

A feature-rich Discord bot for managing a Minecraft server community. This bot provides server status, player info, role management, a counting game, and more, with both prefix and slash command support.

## Features
- **Minecraft Server Integration**: Shows server status, online players, and IP.
- **Counting Game**: Fun counting game with reset/don't reset options.
- **Role Management**: Add/remove roles for members, bots, or all humans.
- **Server Info**: Displays server and role information.
- **Leave Notifications**: Notifies when members leave the server.
- **Support Command**: Provides a support channel link.
- **Result Announcement**: Announces mod application results.
- **Custom Help Command**: Lists all available commands.

## Commands
- `r!ip` / `/ip` — Show Minecraft server IP
- `r!ping` / `/ping` — Show bot latency
- `r!status` / `/status` — Show server online/offline status
- `r!players` / `/players` — List online players
- `r!support` / `/support` — Support info
- `r!setchannel [#channel] reset/dontreset` / `/setchannel` — Set counting game channel
- `r!serverinfo` / `/serverinfo` — Server info
- `r!roleinfo [@role]` / `/roleinfo` — Role info
- `r!addrole` / `/addrole` — Add role to members
- `r!removerole` / `/removerole` — Remove role from member
- `r!leave [#channel]` / `/leave` — Set leave notification channel
- `r!help` / `/help` — Show help menu

## Setup Instructions

1. **Clone or Download** this repository and place `bot8.py` in your working directory.
2. **Install Python 3.8+** (if not already installed).
3. **Install Dependencies:**
   ```bash
   pip install discord.py mcstatus python-dotenv
   ```
4. **Create a `.env` file** in the same directory as `bot8.py` with the following variables:
   ```env
   DISCORD_TOKEN=your_discord_bot_token
   MINECRAFT_SERVER_IP=your.minecraft.server.ip
   MINECRAFT_SERVER_PORT=25565
   ```
   Replace the values with your actual bot token and Minecraft server details.
5. **Run the bot:**
   ```bash
   python bot8.py
   ```

## Environment Variables
- `DISCORD_TOKEN`: Your Discord bot token (keep this secret!)
- `MINECRAFT_SERVER_IP`: The IP address of your Minecraft server
- `MINECRAFT_SERVER_PORT`: The port of your Minecraft server (default: 25565)

## Data Files
- `counting_game_data.json`: Stores counting game state per server
- `leave_channels.json`: Stores leave notification channel per server

These files are auto-created and managed by the bot.

## Dependencies
- [discord.py](https://pypi.org/project/discord.py/)
- [mcstatus](https://pypi.org/project/mcstatus/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

## Notes
- Do **not** share your `.env` file or bot token publicly.
- Make sure your bot has the necessary permissions (manage roles, read/send messages, etc.) in your Discord server.
- For slash commands, the bot will auto-sync on startup.

## License
This project is for personal/community use. Adapt as needed for your server! 