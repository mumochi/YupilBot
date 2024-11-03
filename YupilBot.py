import sys
import discord
from discord import app_commands as ac
from discord.ext import commands
import deepl
import configparser
import os
from dotenv import load_dotenv
from Utils import get_server_id
from TicketTool.TicketComponents import Buttons
from Commands import Yommands
from TicketTool.TicketTool import TicketTool
from EventListeners import Yisteners


# Set environment and read config file
if os.getenv('YUPIL_ENV') != "prod":
    load_dotenv(".env.local")
else:
    load_dotenv(".env")
config = configparser.ConfigParser()
config.read('config.ini')

# Set bot intents and bot configuration
intents = discord.Intents.default() 
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix = '/', intents = intents, max_messages = int(config[os.getenv('YUPIL_ENV')]['cache_size']))
tree = bot.tree

# Set channels
try:
    welcome_channel_id = int(config[os.getenv('YUPIL_ENV')]['welcome_channel'])
    helpdesk_channel_id = int(config[os.getenv('YUPIL_ENV')]['helpdesk_channel'])
except:
    # temp until I add these to my config/test server - star
    welcome_channel_id = 000000000000
    helpdesk_channel_id = 000000000000

log_channel_id = int(config[os.getenv('YUPIL_ENV')]['log_channel'])


# DeepL authentication
auth_key = os.getenv('DEEPL_API_TOKEN')

try:
    translator = deepl.Translator(auth_key)
except:
    translator = None
    print("Invalid DeepL key - check current key or generate a new one.")

# add extensions/cogs
bot.add_cog(Yommands(bot, translator, log_channel_id))
bot.add_cog(TicketTool(bot))
bot.add_cog(Yisteners(bot, log_channel_id, welcome_channel_id))


# Sync commands
@bot.event
async def on_ready():
    await tree.sync(guild = discord.Object(id = get_server_id()))
    # Retrieve ticket button message ID
    if os.path.isfile("buttons_message_id.txt"):
        button_message_id = int(open("buttons_message_id.txt", "r").readline())
        bot.add_view(view = Buttons(timeout = None), message_id = button_message_id)
    print("Logged in and ready to receive commands.")

# Bot login
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
