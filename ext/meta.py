# Module for manual loading, reloading, and unloading extensions as well as syncing commands

import os
import sys
import discord
from discord.ext import commands
import discord.app_commands as ac

# List acceptable parameter values
# Doesn't allow config.py, helpers.py, or meta.py to be actioned because this will break dynamic extensions, forcing a bot restart
ext_list = (ext.rstrip(".py") for ext in os.listdir("./ext") if ext.endswith(".py") and ext not in ("config.py", "helpers.py", "meta.py"))
act_list = ("load", "reload", "unload")

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
    
class SyncCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @ac.command(
        name="sync",
        description="Manually syncs all bot commands. Use to update commands without restarting the bot."
    )
    async def sync(self, interaction: discord.Interaction) -> None:
        self.bot.tree.clear_commands()
        await self.bot.tree.sync(guild=None)
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ExtCog(bot=bot))
    await bot.add_cog(SyncCog(bot=bot))
    await bot.add_cog(KillCog(bot=bot))