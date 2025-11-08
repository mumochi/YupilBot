# Generate and validate .env and config.ini files for first-time setup

import os
import sys
import configparser
import discord
from discord.ext import commands
from dotenv import load_dotenv
from questionary import select, text

print("---\nStarting first-time bot setup.\n---")
server_id = input("Enter server ID: ")
token = input("Enter bot token: ")

with open(".env", "w") as f:
    f.write(f"DISCORD_SERVER_ID={server_id}\n")
    f.write(f"DISCORD_TOKEN={token}")

# Load from file to ensure the file was created correctly
load_dotenv(".env")
server_id = os.getenv("DISCORD_SERVER_ID")
token = os.getenv("DISCORD_TOKEN")

# Set intents. Make sure that intents and server permissions match what is needed for bot functionality
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Create config.ini from available guild data pulled from bot
@bot.event
async def on_ready() -> None:
    print("Successfully connected.")
    guild = await bot.fetch_guild(int(server_id))
    channels = await guild.fetch_channels()
    channel_names = [channel.name for channel in channels]
    roles = await guild.fetch_roles()
    role_names = [role.name for role in roles]
    
    config = configparser.ConfigParser()
    config.read("templates/config.ini")
    for setting in config["prod"]:
        if "channel" in setting:
            selection = await select(f"Choose a channel for {setting}", choices=channel_names).ask_async()
            channel_id = [channel.id for channel in channels if channel.name == selection][0]
            config["prod"][setting] = str(channel_id)
        elif "role" in setting:
            selection = await select(f"Choose a role for {setting}", choices=role_names).ask_async()
            role_id = [role.id for role in roles if role.name == selection][0]
            config["prod"][setting] = str(role_id)
        elif "int" in config["prod"][setting]:
            selection = await text(f"Enter a value for {setting}: ").ask_async()
            config["prod"][setting] = selection
        elif "True" in config["prod"][setting]:
            selection = await select(f"Make a selection for {setting}", choices=["True", "False"]).ask_async()
            config["prod"][setting] = selection

    with open("config.ini", "w") as configfile:
        config.write(configfile)
    print("Setup complete.")
    await bot.close()


# Minimal setup to test authentication
try:
    bot.run(token=token)
except:
    sys.exit(f"Unable to connect to server {server_id} using token {token}. Please double-check that these are both correct and try again.")
