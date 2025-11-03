# Module for manual loading, reloading, and unloading extensions as well as syncing commands

import os
import re
import sys
import discord
from discord.ext import commands
import discord.app_commands as ac
from typing import Optional
import configparser

# List acceptable parameter values
# Doesn't allow config.py, helpers.py, or meta.py to be actioned because this will break dynamic extensions, forcing a bot restart
ext_list = (ext.rstrip(".py") for ext in os.listdir("./ext") if ext.endswith(".py") and ext not in ("config.py", "helpers.py", "meta.py"))
act_list = ("load", "reload", "unload")
toggle_list = ("disable_external_forwarding", "disable_webcams")

class ExtCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @ac.command(
        name="extensions", 
        description="Manage Yupil Bot extensions. Does not require a bot restart.")
    @ac.describe(
        extension="Name of extension",
        action="Action to perform: load, reload, or unload"
    )
    @ac.choices(
        extension=[ac.Choice(name=ext, value=ext) for ext in ext_list],
        action=[ac.Choice(name=act, value=act) for act in act_list])
    async def extensions(self, interaction: discord.Interaction, extension: str, action: str) -> None:
        extension = extension.rstrip(".py")
        if action == "load":
            try:
                await self.bot.load_extension(f"ext.{extension}")
                await interaction.response.send_message(f"Loaded extension: {extension}", ephemeral=True)
            except commands.ExtensionAlreadyLoaded:
                await interaction.response.send_message(f"\"{extension}\" extension is already loaded.", ephemeral=True)
        elif action == "reload":
            try:
                await self.bot.reload_extension(f"ext.{extension}")
                await interaction.response.send_message(f"Reloaded extension: {extension}", ephemeral=True)
            except commands.ExtensionNotLoaded:
                await interaction.response.send_message(f"\"{extension}\" extension is not loaded. Run this command with the load action to load.", ephemeral=True)
        else:
            try:
                await self.bot.unload_extension(f"ext.{extension}")
                await interaction.response.send_message(f"Unloaded extension: {extension}", ephemeral=True)
            except commands.ExtensionNotLoaded:
                await interaction.response.send_message(f"\"{extension}\" extension is not loaded.", ephemeral=True)

class ToggleCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @ac.command(
        name="toggle",
        description="Toggle bot commands. Changes will be saved to the config.ini file."
    )
    @ac.describe(
        function="Name of function.",
        toggle_state="Enable or disable function."
    )
    @ac.choices(
        function=[ac.Choice(name=cmd, value=cmd) for cmd in toggle_list],
        toggle_state=[ac.Choice(name=state, value=state) for state in ["True", "False"]]
    )
    async def toggle(self, interaction: discord.Interaction, function: str, toggle_state: str) -> None:
        """Enables or disables a bot function."""
        config = configparser.ConfigParser()
        config.read("config.ini")
        if function == "disable_external_forwarding":
            self.bot.config.disable_external_forwarding = True if toggle_state == "True" else False
            for section in config.sections():
                config[section]["disable_external_forwarding"] = toggle_state
            with open("config.ini", "w") as configfile:
                config.write(configfile)
            await interaction.response.send_message(f"Function {function} toggled to \"{toggle_state}\".", ephemeral=True)
        elif function == "disable_webcams":
            self.bot.config.disable_webcams = True if toggle_state == "True" else False
            for section in config.sections():
                config[section]["disable_webcams"] = toggle_state
            with open("config.ini", "w") as configfile:
                config.write(configfile)
            await interaction.response.send_message(f"Function {function} toggled to \"{toggle_state}\".", ephemeral=True)
    
class SyncCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @ac.command(
        name="sync",
        description="Manually syncs all bot commands. Use to update commands without restarting the bot."
    )
    async def sync(self, interaction: discord.Interaction) -> None:
        await self.bot.tree.sync()
        await interaction.response.send_message("Commands synced.", ephemeral=True)

class KillCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @ac.command(
        name = "kill_me",
        description = "You horrible person. What did the lil guy ever do to you?!"
        )
    @ac.describe(
            reason = "Motive for the murder."
    )
    async def kill_me(self, interaction: discord.Interaction, reason: str) -> None:
        """Terminates the program and logs the reason."""
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        deadge = [e for e in self.bot.emojis if e.name == "yuyixDeadge"][0]
        await log_channel.send(f"{interaction.user.global_name} murdered Yupil Bot for: {reason} <:{deadge.name}:{deadge.id}>")
        sys.exit(reason)

class DebugCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @ac.command(
        name = "view_log",
        description = "Sends discord.log tail text as a chat message."
    )
    @ac.describe(
        warnings = "Only show log lines with warnings.",
        errors = "Only show log lines with errors."
    )
    async def view_log(self, interaction: discord.Interaction, warnings: Optional[bool]=False, errors: Optional[bool]=False) -> None:
        """Reads discord.log file and sends tail contents as an embed message."""
        EMBED_MAX = 4096
        DUMMYVAL = "DUMMYVAL1234"
        
        warn_pattern = "warn" if warnings is True else DUMMYVAL
        error_pattern = "error" if errors is True else DUMMYVAL

        if warnings is True or errors is True:
            with open("discord.log", "r") as f:
                lines = "".join(line for line in f.readlines() if re.search(warn_pattern, line.lower()) or re.search(error_pattern, line.lower())) 
        
        else:
            with open("discord.log", "r") as f:
                lines = "".join(f.readlines())         

        if len(lines) > EMBED_MAX:
            start_index = lines.find("\n", len(lines)-EMBED_MAX)
            lines = lines[start_index:len(lines)-1] 

        elif len(lines) == 0:
            lines = "No entries available for query."  

        embed = discord.Embed(title="discord.log",
                                    description=lines,
                                    color=self.bot.helpers.yupil_color)

        await interaction.response.send_message(embed=embed)
  

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ExtCog(bot=bot))
    await bot.add_cog(ToggleCog(bot=bot))
    await bot.add_cog(SyncCog(bot=bot))
    await bot.add_cog(KillCog(bot=bot))
    await bot.add_cog(DebugCog(bot=bot))
    