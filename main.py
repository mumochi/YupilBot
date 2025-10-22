import os
import logging
import discord
from discord.ext import commands
from ext.config import ConfigManager
from ext.helpers import Helpers

# Set intents. Make sure that intents and server permissions match what is needed for bot functionality
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True

config = ConfigManager(config_file="config.ini")

# Bot setup
# Create the setup hook which will load all extensions in the ./ext directory and sync commands
ext_list = [ext.rstrip(".py") for ext in os.listdir("./ext") if ext.endswith(".py") and ext != "config.py" and ext != "helpers.py"]

class BotClient(commands.Bot):
    def __init__(self, *, command_prefix: str, intents: discord.Intents, max_messages: int) -> None:
        super().__init__(command_prefix=command_prefix, intents=intents, max_messages=max_messages)
        self.config = config
        self.helpers = Helpers()

    async def setup_hook(self) -> None:
        for ext in ext_list:
            await self.load_extension(f"ext.{ext}")
        self.tree.clear_commands()
        await self.tree.sync()
        
bot = BotClient(command_prefix='/', intents=intents, max_messages=config.max_messages)

# Login and run with simple logging enabled
@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user.name}")
    print(f"Loaded extensions: {list(bot.extensions.keys())}")
    print("---------------------------------")
    cog = bot.get_cog("ListenCog")
    await cog.run_member_checks.start()

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
bot.run(token=bot.config.token, log_handler=handler)