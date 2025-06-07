import discord
from discord.ext import commands
from discord import app_commands  # For slash commands
from mcstatus import JavaServer
import os
import json
from dotenv import load_dotenv
import re
import asyncio
from discord.ui import Button, View

load_dotenv()

# Load configurations
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MINECRAFT_SERVER_IP = os.getenv('MINECRAFT_SERVER_IP')
MINECRAFT_SERVER_PORT = int(os.getenv('MINECRAFT_SERVER_PORT'))
SERVER_VERSION = "1.21.1"  # Update with the actual server version

# Hardcoded values
DISCORD_INVITE = "https://discord.gg/krdHGQsne4"
SERVER_MODERATORS = ["𝓡𝓸𝓬𝓴𝔂_𝓡𝓾𝓽𝔀𝓲𝓴", "kabashikun"]
SUPPORT_CHANNEL_LINK = "https://discord.com/channels/894902529039687720/960196810796847134"

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Enable member intents for role commands
bot = commands.Bot(command_prefix='r!', intents=intents, help_command=None)  # Custom help command
tree = bot.tree  # For slash commands

# Initialize Minecraft server status
minecraft_server = JavaServer.lookup(f"{MINECRAFT_SERVER_IP}:{MINECRAFT_SERVER_PORT}")

# Load and save counting game data from/to JSON file
def load_game_data():
    if os.path.exists('counting_game_data.json'):
        with open('counting_game_data.json', 'r') as f:
            return json.load(f)
    return {}

def save_game_data(data):
    with open('counting_game_data.json', 'w') as f:
        json.dump(data, f, indent=4)

# Initialize the game data dictionary
game_data = load_game_data()

# Function to validate if the message is a valid number or expression
def is_valid_count(message, expected_number):
    try:
        if int(message.content) == expected_number:
            return True
    except ValueError:
        pass

    try:
        result = eval(message.content)
        if result == expected_number:
            return True
    except Exception:
        pass
    return False

# Track leave notification channel
leave_channels = {}

def save_leave_channels():
    with open('leave_channels.json', 'w') as f:
        json.dump(leave_channels, f, indent=4)

def load_leave_channels():
    global leave_channels
    if os.path.exists('leave_channels.json'):
        with open('leave_channels.json', 'r') as f:
            leave_channels = json.load(f)

load_leave_channels()

# Leave channel setup
@bot.command(name='leave')
@commands.has_permissions(administrator=True)
async def set_leave_channel(ctx, channel: discord.TextChannel):
    leave_channels[str(ctx.guild.id)] = channel.id
    save_leave_channels()
    await ctx.send(f"Leave notifications will be sent to {channel.mention}")

@tree.command(name="leave", description="Set the channel for leave notifications")
@app_commands.describe(channel="The channel for leave notifications")
async def slash_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    leave_channels[str(interaction.guild.id)] = channel.id
    save_leave_channels()
    await interaction.response.send_message(f"Leave notifications will be sent to {channel.mention}")

# Send leave notification when a member leaves the server
@bot.event
async def on_member_remove(member):
    guild_id = str(member.guild.id)
    if guild_id in leave_channels:
        channel = bot.get_channel(int(leave_channels[guild_id]))
        if channel:
            embed = discord.Embed(
                title="Member Left",
                description=f"{member.mention} ({member.name}#{member.discriminator}) has left the server.",
                color=discord.Color.red()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await tree.sync()

@bot.event
async def on_message(message):
    global game_data

    if message.guild is None:
        await bot.process_commands(message)
        return

    guild_id = str(message.guild.id)

    if guild_id in game_data and message.channel.id == game_data[guild_id]['counting_channel_id']:
        if message.author != bot.user:
            current_number = game_data[guild_id]['current_number']
            last_user_id = game_data[guild_id]['last_user_id']

            reset_on_error = game_data[guild_id].get('reset_on_error', 'reset')

            if is_valid_count(message, current_number):
                if last_user_id == message.author.id:
                    embed = discord.Embed(
                        title="Error",
                        description=f"{message.author.mention}, you cannot send two numbers in a row!",
                        color=discord.Color.red()
                    )
                    await message.channel.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Correct Count",
                        description=f"{message.author.mention} counted {current_number} correctly!",
                        color=discord.Color.green()
                    )
                    await message.channel.send(embed=embed)
                    game_data[guild_id]['current_number'] += 1
                    game_data[guild_id]['last_user_id'] = message.author.id
                    save_game_data(game_data)
            elif message.content.isdigit() or re.match(r'[\d\+\-\*/]+', message.content):
                embed = discord.Embed(
                    title="Wrong Number",
                    description=f"{message.author.mention}, wrong number or expression!",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                if reset_on_error == 'reset':
                    game_data[guild_id]['current_number'] = 1
                    await message.channel.send(embed=discord.Embed(
                        title="Counting Game",
                        description=f"Counting restarted! Start from 1.",
                        color=discord.Color.green()
                    ))
                game_data[guild_id]['last_user_id'] = None
                save_game_data(game_data)
    await bot.process_commands(message)

# Sync Bot Commands    
@bot.command(name='sync')
@commands.is_owner()
async def sync_commands(ctx):
    await tree.sync()
    await ctx.send("Slash commands have been synced.")
    
# Counting game setup
@bot.command(name='setchannel', aliases=['setch'])
@commands.has_permissions(administrator=True)
async def setchannel(ctx, channel: discord.TextChannel, reset_option: str):
    global game_data
    guild_id = str(ctx.guild.id)

    if reset_option not in ['reset', 'dontreset']:
        await ctx.send("Invalid option! Use 'reset' to reset on a wrong number, or 'dontreset' to continue counting.")
        return

    game_data[guild_id] = {
        'counting_channel_id': channel.id,
        'current_number': 1,
        'last_user_id': None,
        'reset_on_error': reset_option
    }
    save_game_data(game_data)

    embed = discord.Embed(
        title="Counting Game",
        description=f"Counting game started in {channel.mention} with reset option {reset_option}! Start counting from 1.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@tree.command(name="setchannel", description="Set the counting game channel with reset option")
@app_commands.describe(channel="The channel to set", reset_option="Choose between reset or dontreset")
@app_commands.choices(reset_option=[
    app_commands.Choice(name="reset", value="reset"),
    app_commands.Choice(name="dontreset", value="dontreset")
])
async def slash_setchannel(interaction: discord.Interaction, channel: discord.TextChannel, reset_option: str):
    guild_id = str(interaction.guild.id)

    game_data[guild_id] = {
        'counting_channel_id': channel.id,
        'current_number': 1,
        'last_user_id': None,
        'reset_on_error': reset_option
    }
    save_game_data(game_data)

    embed = discord.Embed(
        title="Counting Game",
        description=f"Counting game started in {channel.mention} with reset option {reset_option}! Start counting from 1.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# Server info
@bot.command(name='serverinfo')
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"{guild.name} Server Information", color=discord.Color.blue())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(name="ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Created At", value=guild.created_at.strftime('%Y-%m-%d %I:%M %p'), inline=True)

    await ctx.send(embed=embed)

@tree.command(name="serverinfo", description="Displays server information")
async def slash_serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"{guild.name} Server Information", color=discord.Color.blue())

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(name="ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Created At", value=guild.created_at.strftime('%Y-%m-%d %I:%M %p'), inline=True)

    await interaction.response.send_message(embed=embed)

# Role info
@bot.command(name='roleinfo')
async def roleinfo(ctx, role: discord.Role):
    permissions = ', '.join([perm[0].replace('_', ' ').title() for perm in role.permissions if perm[1]])
    embed = discord.Embed(title=f"Role Information - {role.name}", color=role.color)
    embed.add_field(name="ID", value=role.id, inline=True)
    embed.add_field(name="Permissions", value=f"`{permissions or 'None'}`", inline=False)
    embed.add_field(name="Created At", value=role.created_at.strftime('%Y-%m-%d %I:%M %p'), inline=True)
    await ctx.send(embed=embed)

@tree.command(name="roleinfo", description="Displays role information")
@app_commands.describe(role="The role to display information about")
async def slash_roleinfo(interaction: discord.Interaction, role: discord.Role):
    permissions = ', '.join([perm[0].replace('_', ' ').title() for perm in role.permissions if perm[1]])
    embed = discord.Embed(title=f"Role Information - {role.name}", color=role.color)
    embed.add_field(name="ID", value=role.id, inline=True)
    embed.add_field(name="Permissions", value=f"`{permissions or 'None'}`", inline=False)
    embed.add_field(name="Created At", value=role.created_at.strftime('%Y-%m-%d %I:%M %p'), inline=True)
    await interaction.response.send_message(embed=embed)

# Add and remove role
@bot.command(name='addrole')
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member_type: str, role: discord.Role, member: discord.Member = None):
    if member_type == 'human':
        humans = [member for member in ctx.guild.members if not member.bot]
        for human in humans:
            if ctx.author.top_role <= role:
                await ctx.send(embed=discord.Embed(title="Error", description=f"Cannot add role {role.name} because your role is lower or equal to the role.", color=discord.Color.red()))
                return
            await human.add_roles(role)
        await ctx.send(embed=discord.Embed(title="Add Role", description=f"Added {role.name} to all human members.", color=discord.Color.green()))
    elif member_type == 'bots':
        bots = [member for member in ctx.guild.members if member.bot]
        for bot in bots:
            if ctx.author.top_role <= role:
                await ctx.send(embed=discord.Embed(title="Error", description=f"Cannot add role {role.name} because your role is lower or equal to the role.", color=discord.Color.red()))
                return
            await bot.add_roles(role)
        await ctx.send(embed=discord.Embed(title="Add Role", description=f"Added {role.name} to all bots.", color=discord.Color.green()))
    elif member_type == 'member' and member:
        if ctx.author.top_role <= role:
            await ctx.send(embed=discord.Embed(title="Error", description=f"Cannot add role {role.name} because your role is lower or equal to the role.", color=discord.Color.red()))
            return
        await member.add_roles(role)
        await ctx.send(embed=discord.Embed(title="Add Role", description=f"Added {role.name} to {member.mention}.", color=discord.Color.green()))
    else:
        await ctx.send("Invalid member type! Use 'human', 'bots', or 'member'.")

@tree.command(name="addrole", description="Adds a role to all humans, bots, or a specific member")
@app_commands.describe(member_type="Type of members: humans, bots, or a single member", role="The role to add", member="The member to assign the role to if 'member' is chosen")
@app_commands.choices(member_type=[
    app_commands.Choice(name="human", value="human"),
    app_commands.Choice(name="bots", value="bots"),
    app_commands.Choice(name="member", value="member")
])
async def slash_addrole(interaction: discord.Interaction, member_type: str, role: discord.Role, member: discord.Member = None):
    if member_type == 'human':
        humans = [member for member in interaction.guild.members if not member.bot]
        for human in humans:
            if interaction.user.top_role <= role:
                await interaction.response.send_message(embed=discord.Embed(title="Error", description=f"Cannot add role {role.name} because your role is lower or equal to the role.", color=discord.Color.red()))
                return
            await human.add_roles(role)
        await interaction.response.send_message(embed=discord.Embed(title="Add Role", description=f"Added {role.name} to all human members.", color=discord.Color.green()))
    elif member_type == 'bots':
        bots = [member for member in interaction.guild.members if member.bot]
        for bot in bots:
            if interaction.user.top_role <= role:
                await interaction.response.send_message(embed=discord.Embed(title="Error", description=f"Cannot add role {role.name} because your role is lower or equal to the role.", color=discord.Color.red()))
                return
            await bot.add_roles(role)
        await interaction.response.send_message(embed=discord.Embed(title="Add Role", description=f"Added {role.name} to all bots.", color=discord.Color.green()))
    elif member_type == 'member' and member:
        if interaction.user.top_role <= role:
            await interaction.response.send_message(embed=discord.Embed(title="Error", description=f"Cannot add role {role.name} because your role is lower or equal to the role.", color=discord.Color.red()))
            return
        await member.add_roles(role)
        await interaction.response.send_message(embed=discord.Embed(title="Add Role", description=f"Added {role.name} to {member.mention}.", color=discord.Color.green()))
    else:
        await interaction.response.send_message("Invalid member type! Use 'human', 'bots', or 'member'.")

@bot.command(name='removerole')
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    embed = discord.Embed(title="Remove Role", description=f"Removed {role.name} from {member.mention}.", color=discord.Color.red())
    await ctx.send(embed=embed)

@tree.command(name="removerole", description="Removes a role from a specific member")
@app_commands.describe(member="The member to remove the role from", role="The role to remove")
async def slash_removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    embed = discord.Embed(title="Remove Role", description=f"Removed {role.name} from {member.mention}.", color=discord.Color.red())
    await interaction.response.send_message(embed=embed)

# IP, Ping, Status, Players, Support Commands

# Ip Command (r!ip and /ip)
@bot.command(name='ip')
async def ip(ctx):
    embed = discord.Embed(
        title="Server IP Address",
        description=f"mc.rutwikdev.com",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@tree.command(name="ip", description="Shows the Minecraft server IP address")
async def slash_ip(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Server IP Address",
        description=f"mc.rutwikdev.com",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)


# Ping Command (r!ping and /ping)
@bot.command(name='ping', aliases=['p'])
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="Bot Latency",
        description=f"Pong! Latency is {latency} ms.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@tree.command(name="ping", description="Shows the bot's latency")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="Bot Latency",
        description=f"Pong! Latency is {latency} ms.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)
    
    
# Status Command (r!status and /status)
@bot.command(name='status', aliases=['st'])
async def status(ctx):
    try:
        status = minecraft_server.status()
        embed = discord.Embed(
            title="Server Status",
            description="The server is currently **Online**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Players Online", value=f"{status.players.online}/{status.players.max}")
    except Exception as e:
        embed = discord.Embed(
            title="Server Status",
            description="The server is currently **Offline**.",
            color=discord.Color.red()
        )
        print(f"Error fetching server status: {e}")
    
    await ctx.send(embed=embed)

@tree.command(name="status", description="Shows whether the server is online or offline")
async def slash_status(interaction: discord.Interaction):
    try:
        status = minecraft_server.status()
        embed = discord.Embed(
            title="Server Status",
            description="The server is currently **Online**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Players Online", value=f"{status.players.online}/{status.players.max}")
    except Exception as e:
        embed = discord.Embed(
            title="Server Status",
            description="The server is currently **Offline**.",
            color=discord.Color.red()
        )
        print(f"Error fetching server status: {e}")
    
    await interaction.response.send_message(embed=embed)


# Players Command (r!players and /players)
@bot.command(name='players', aliases=['pl'])
async def players(ctx):
    try:
        status = await asyncio.get_event_loop().run_in_executor(None, minecraft_server.status)
        player_list = ', '.join(player.name for player in status.players.sample) if status.players.sample else 'No players online'
        embed = discord.Embed(
            title="Players Online",
            description=f"Players currently online: {player_list}",
            color=discord.Color.blue()
        )
    except Exception as e:
        embed = discord.Embed(
            title="Error",
            description="Unable to retrieve player list.",
            color=discord.Color.red()
        )
        print(f"Error fetching player list: {e}")
    await ctx.send(embed=embed)

@tree.command(name="players", description="Shows the players currently online on the Minecraft server")
async def slash_players(interaction: discord.Interaction):
    try:
        status = await asyncio.get_event_loop().run_in_executor(None, minecraft_server.status)
        player_list = ', '.join(player.name for player in status.players.sample) if status.players.sample else 'No players online'
        embed = discord.Embed(
            title="Players Online",
            description=f"Players currently online: {player_list}",
            color=discord.Color.blue()
        )
    except Exception as e:
        embed = discord.Embed(
            title="Error",
            description="Unable to retrieve player list.",
            color=discord.Color.red()
        )
        print(f"Error fetching player list: {e}")
    
    await interaction.response.send_message(embed=embed)


# Support Command (r!support and /support)
@bot.command(name='support')
async def support(ctx):
    """Sends support message."""
    embed = discord.Embed(
        title="Server Support",
        description=f"If you need support for the server, please contact the server admins or visit our [Support Channel]({SUPPORT_CHANNEL_LINK}).",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@tree.command(name="support", description="Provides server support information")
async def slash_support(interaction: discord.Interaction):
    """Slash command version for support."""
    embed = discord.Embed(
        title="Server Support",
        description=f"If you need support for the server, please contact the server admins or visit our [Support Channel]({SUPPORT_CHANNEL_LINK}).",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)


# Result Declaration Command
@tree.command(name="result", description="Announces the result of the mod application")
async def slash_result(interaction: discord.Interaction):
    # List of winners and non-selected with reasons
    selected = [
        "Nimar", 
        "yokoso_watashinosoulsociety"
    ]
    not_selected = [
        ("SussyGamer", "Good contacts but base answers rejected"), 
        ("im___d", "No base"),
        ("Quartz.io", "Rejected as no experience"),
        ("lemuni", "No experience, rejected"),
        ("Oni chan", "No experience, rejected"),
        ("sukuna_or_yuji", "Rejected age 12"),
        ("omarbaba8888", "Rejected age 12"),
        ("itztheduck19", "Can help with time zone issues but base answers rejected"),
        ("ElectricDivyansh", "OK answers but still rejected"),
        ("Konner_leesir", "Rejected due to low experience")
    ]

    # Create the embed for result declaration
    embed = discord.Embed(
        title="Mod Application Results",
        description="Thank you to everyone who applied for the mod position. Below are the results of the selection process.",
        color=discord.Color.blue()
    )

    # Add the winners
    winners = '\n'.join([f"✅ {name}" for name in selected])
    embed.add_field(name="Selected Applicants", value=winners if winners else "No one was selected", inline=False)

    # Add the not selected with reasons
    losers = '\n'.join([f"❌ {name} - {reason}" for name, reason in not_selected])
    embed.add_field(name="Not Selected Applicants", value=losers if losers else "Everyone was selected", inline=False)

    # Send the embed
    await interaction.response.send_message(embed=embed)

# Updated Help Command with Bot Icon
@bot.command(name='help', aliases=['h'])
async def help_command(ctx):
    bot_icon = ctx.bot.user.avatar.url if ctx.bot.user.avatar else ""
    embed = discord.Embed(
        title=f"🤖 Bot Commands",
        description="Here are the available commands:",
        color=discord.Color.blue()
    )

    embed.add_field(name=":gear: Server Commands", value="`r!ip`: Shows the Minecraft server IP address.\n"
                                                   "`r!ping`: Shows the bot's latency.\n"
                                                   "`r!status`: Shows whether the server is online or offline.\n"
                                                   "`r!players`: Lists the players currently online.\n"
    											   "`r!support`: Provides support contact information.", inline=False)

    embed.add_field(name=":video_game: Fun Game Commands", value="`r!setchannel [#channel] reset/dontreset`: Sets the counting game channel.\n"
                                                    "`r!pin`: Sends a message for users looking for the Bookworm Pin.\n", inline=False)

    embed.add_field(name=":gear: Admin Commands", value="`r!serverinfo`: Shows server information.\n"
                                                  "`r!roleinfo [@role]`: Displays information about a role.\n"
                                                  "`r!addrole [@member] [@role]`: Adds a role to a member.\n"
                                                  "`r!removerole [@member] [@role]`: Removes a role from a member.\n"
                                                  "`r!userinfo [@member]`: Shows detailed information about a user.\n"
                                                  "`r!leave [#channel]`: Shows detailed information about a user.", inline=False)

    await ctx.send(embed=embed)

# Slash command version of help
@tree.command(name="help", description="Show help menu for bot commands")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"🤖 Bot Commands",
        description="Here are the available commands:",
        color=discord.Color.blue()
    )

    embed.add_field(name=":gear: Server Commands", value="`/ip`: Shows the Minecraft server IP address.\n"
                                                   "`/ping`: Shows the bot's latency.\n"
                                                   "`/status`: Shows whether the server is online or offline.\n"
                                                   "`/players`: Lists the players currently online.\n"
    											   "`/support`: Provides support contact information.", inline=False)

    embed.add_field(name=":video_game: Fun Game Commands", value="`/setchannel [#channel] reset/dontreset`: Sets the counting game channel.\n"
                                                    "`/pin`: Sends a message for users looking for the Bookworm Pin.\n", inline=False)

    embed.add_field(name=":gear: Admin Commands", value="`/serverinfo`: Shows server information.\n"
                                                  "`/roleinfo [@role]`: Displays information about a role.\n"
                                                  "`/addrole [@member] [@role]`: Adds a role to a member.\n"
                                                  "`/removerole [@member] [@role]`: Removes a role from a member.\n"
                                                  "`/userinfo [@member]`: Shows detailed information about a user.\n"
                                                  "`/leave [#channel]`: Shows detailed information about a user.", inline=False)

    await interaction.response.send_message(embed=embed)

# Run the bot
bot.run(DISCORD_TOKEN)
