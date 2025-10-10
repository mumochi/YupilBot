# Module for mod tools

import discord
from discord.ext import commands
import discord.app_commands as ac
import datetime as dt
import asyncio
import requests
from typing import Optional

class MessageSnowflake(discord.abc.Snowflake):
    def __init__(self, id: int) -> None:
        self.id = id

class ModCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # PermissionOverwrite class with user and context-specific permissions
        self.HideChannelPerms = discord.PermissionOverwrite(read_messages=False, view_channel=False)
        self.ShowChannelPerms = discord.PermissionOverwrite(read_messages=True)

    # Log mod actions and DM members to communicate mod decisions
    async def log_dm(self, interaction: discord.Interaction, action: str, member: discord.Member, message: Optional[str]=None) -> None:
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        priority_log_channel = self.bot.get_channel(self.bot.config.priority_log_channel)
        timestamp = dt.datetime.now()
        embed = discord.Embed(
            title=f"Mod action: {action}", 
            description=f"Mod action `{action}` applied to {member.mention} by {interaction.user.display_name}",
            color=discord.Color.red(),
            timestamp=timestamp
            )
        avatar = await self.bot.helpers.valid_avatar(member=member)
        embed.set_author(name=member, icon_url=avatar)
        await priority_log_channel.send(embed=embed)

        if message is not None:
            message = message.replace(r'\n', '\n')
            embed = discord.Embed(title="Mod Team Message", description=f"Hello {member.mention},\n\n{message}\n\n ", color=self.bot.helpers.yupil_color)
            embed.set_footer(text="`This is a Yupil Bot message on behalf of the Mod Team. If you would like to reach out to a member of the Mod Team, please create a ticket on the server using our ticket system.`")
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            try:
                await member.send(embed=embed)
                embed.title = f"Mod action `{action}` applied to {member.display_name}. Reason sent as a DM:"
                message_log = await log_channel.send(embed=embed)
                await interaction.response.send_message(f"DM sent to {member.display_name}. View log: {message_log.jump_url}", ephemeral=True)
            except:
                await interaction.response.send_message(f"DM failed to send. {member.display_name} may have DMs turned off.", ephemeral=True)
        else:
            await interaction.response.send_message(f"`{action}` applied to {member.display_name}")

    async def toggle_channel_visibility(self, member: discord.Member, toggle: str) -> None:
        """Sets all channel overrides to restrict visibility for user."""
        # Iteratively restrict access to every server text, voice, and forum channel
        guild = member.guild
        channels = guild.text_channels + guild.voice_channels + guild.forums
        if toggle == "off":
            for channel in channels:
                try:
                    if channel.permissions_for(guild.me).view_channel:
                        await channel.set_permissions(member, overwrite=self.HideChannelPerms)
                except:
                    print(f"No access to {channel}")
        else:
            for channel in channels:
                try:
                    if channel.permissions_for(guild.me).view_channel:
                        await channel.set_permissions(member, overwrite=None)
                except:
                    print(f"No access to {channel}")

    # Timeout a member
    @ac.command(
        name="yb-timeout",
        description="Times out a member for the specified duration in minutes."
    )
    @ac.describe(
        member="Member to timeout",
        duration="Duration to timeout in minutes (default: 15 minutes)",
        reason="Reason for the timeout; attempts to send DM to member (optional, default: None)"
    )
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: Optional[int]=15, reason: Optional[str]=None) -> None:
        penalty = dt.timedelta(minutes=duration)
        await member.timeout(penalty, reason=reason)
        await self.log_dm(interaction=interaction, action="timeout", message=reason, member=member)

    # Kick a likely/suspected bot
    @ac.command(
        name="botkick",
        description="Standardized messaging and kick handling for likely bots."
    )
    @ac.describe(
            member = "Member to kick."
    )
    async def botkick(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Standardized messaging and kick handling for likely bots."""
        timestamp = dt.datetime.now()
        reason = "Discord has detected unusual activity on your account consistent with bot and/or spam messages. Please send in a support ticket if you believe this was done in error."
        welcome_channel = self.bot.get_channel(self.bot.config.welcome_channel)

        async for m in welcome_channel.history(limit=20):
                if m.author.id == member.id:
                    await m.delete()

        # Must send DM before kicking or it won't be sendable
        await self.log_dm(interaction=interaction, action="botkick", member=member, message=reason)
        await interaction.guild.kick(member)

    # Purge messages from a channel or member
    # NOTE: Member purge is an experimental feature based on unstable spec here: https://github.com/discord/discord-api-docs/discussions/3216
    @ac.command(
        name="yb-purge",
        description="Purge messages from a channel or member."
    )
    @ac.describe(
        messages="Number of messages to purge (integer, max: 50)",
        target_channel="Channel to purge messages from (optional, leave blank to purge messages from a member across all channels)",
        target_member="Member to purge messages from (optional, experimental feature)"
    )
    async def purge(
        self, interaction: discord.Interaction, messages: int, 
        target_channel: discord.TextChannel=None, target_member: discord.Member=None) -> None:
        
        await interaction.response.defer(ephemeral=True, thinking=True)

        if messages > 50:
            messages = 50

        if target_channel is not None and target_member is None:
            await target_channel.purge(limit=messages, bulk=True) # Use bulk to help avoid rate-limiting
            await interaction.followup.send(f"Purged {messages} messages from {target_channel.jump_url}.", ephemeral=True)

        elif target_channel is not None and target_member is not None:
            i = 0
            async for m in target_channel.history(limit=100):
                if i < messages and m.author == target_member:
                    await m.delete()
                    await asyncio.sleep(1) # Help to avoid rate-limiting
                    i += 1
            await interaction.followup.send(f"Purged {i} messages from {target_member.mention} in {target_channel.jump_url}.", ephemeral=True)

        elif target_channel is None and target_member is not None:
            # Experimental, may break if Discord changes API spec
            url = f"https://discord.com/api/v10/guilds/{self.bot.config.server_id}/messages/search?author_id={target_member.id}&sort_by=timestamp&sort_order=desc&limit={messages}"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bot {self.bot.config.token}'
            }

            try:
                req = requests.get(url=url, headers=headers)
                req = req.json()["messages"]
                for m in req:
                    channel = self.bot.get_channel(int(m[0]["channel_id"]))
                    message = MessageSnowflake(id=int(m[0]["id"]))
                    await channel.delete_messages([message])
                await interaction.followup.send(f"{messages} messages from {target_member.display_name} purged.", ephemeral=True)
                await self.log_dm(interaction=interaction, action="purge", member=target_member, message=None)
            except BaseException as e:
                await interaction.followup.send(
                    f"Failed to purge messages. This is an experimental feature; please let us know if it failed.\nError: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send("Please specify a channel and/or member to purge.", ephemeral=True)

    @ac.command(
        name="yb-softban",
        description="Bans and immediately unbans a member."
    )
    @ac.describe(
        member="Member to softban",
        reason="Reason for the softban; attempts to send a DM to member (optional, default: None)"
    )
    async def softban(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str]=None) -> None:
        # Must send DM before banning or it won't be sendable
        await self.log_dm(interaction=interaction, action="softban", member=member, message=reason)
        await member.ban()
        await member.unban()

    @ac.command(
        name="yb-ban",
        description="Bans a member, intended to be permanent."
    )
    @ac.describe(
        member="Member to ban",
        reason="Reason for the ban; attempts to send a DM to member (optional, default: None)"
    )
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str]=None) -> None:
        # Must send DM before banning or it won't be sendable
        await self.log_dm(interaction=interaction, action="ban", member=member, message=reason)
        await member.ban()

    @ac.command(
            name = "restrict",
            description = "Restricts a member from viewing all channels."
    )
    #@ac.checks.has_role(permitted_role)
    @ac.describe(
        member = "Member to restrict"
    )
    async def restrict(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Restricts a member from viewing all channels."""
        timestamp = dt.datetime.now()
        await interaction.response.send_message(f"Restricting {member.display_name}. This may take some time.", ephemeral=True)
        await self.toggle_channel_visibility(member=member, toggle="off")
        await self.log_dm(interaction=interaction, action="restrict", member=member, message=None)
        await interaction.delete_original_response()

    @ac.command(
            name = "unrestrict",
            description = "Unrestricts a member to restore channel access."
    )
    #@ac.checks.has_role(permitted_role)
    @ac.describe(
        member = "Member to unrestrict"
    )
    async def unrestrict(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Restricts a user from viewing all channels."""
        timestamp = dt.datetime.now()
        await interaction.response.send_message(f"Unrestricting {member.display_name}. This may take some time.", ephemeral=True)
        await self.toggle_channel_visibility(member=member, toggle="on")
        await self.log_dm(interaction=interaction, action="unrestrict", member=member, message=None)
        await interaction.delete_original_response()
        

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModCog(bot=bot))