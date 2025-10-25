# Module for listening and responding to events

import discord
from discord.ext import commands, tasks
import discord.app_commands as ac
import datetime as dt
import asyncio
import requests
from collections import deque

# Parameters for anti-spam detection
CACHE_SIZE = 3
MESSAGE_AGE = 60

class MessageSnowflake(discord.abc.Snowflake):
    def __init__(self, created_at: dt.datetime, author: discord.Member, content: str) -> None:
        self.author = author
        self.created_at = created_at
        self.content = content    

class RoleSnowflake(discord.abc.Snowflake):
    def __init__(self, id: int) -> None:
        self.id = id

class ListenCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.all_role = self.bot.config.all_role
        self.vc_role = self.bot.config.vc_role
        self.message_cache = deque(maxlen=CACHE_SIZE)
        init_message = []
        for i in range(CACHE_SIZE):
            author = RoleSnowflake(id=f"{i}")
            init_message.append(MessageSnowflake(created_at=dt.datetime.now(dt.timezone.utc), author=author, content=f"content{i}"))
        self.message_cache.extend(init_message)

    # Log spammer detection
    async def log_spammer(self, member: discord.Member) -> None:
        timestamp = dt.datetime.now()
        priority_log_channel = self.bot.get_channel(self.bot.config.priority_log_channel)
        embed = discord.Embed(title="Potential Spammer Detected",
                            description=f"{member.mention} has been detected by Discord as a potential spammer.",
                            color=discord.Color.orange(),
                            timestamp=timestamp)
        avatar = await self.bot.helpers.valid_avatar(member=member)
        embed.set_author(name=member.display_name, icon_url=avatar)
        embed.set_footer(text = f"Member: {member.name} | ID: {member.id}")
        # Avoid repeating message log
        messages = [m async for m in priority_log_channel.history(limit=1)]
        for m in messages:
            if len(m.embeds) == 0 or m.embeds[0].footer.text is None or str(member.id) not in m.embeds[0].footer.text or (str(member.id) in m.embeds[0].footer.text and embed.description != m.embeds[0].description):
                await priority_log_channel.send(embed=embed)

    async def detect_spam(self, messages: deque, time: dt.datetime) -> None:
        authors = [m.author.id for m in messages]
        contents = [m.content for m in messages]
        times = [(m.created_at - messages[0].created_at).seconds < MESSAGE_AGE for m in messages]

        if len(set(authors)) == 1 and len(set(contents)) == 1 and all(times):
            priority_log_channel = self.bot.get_channel(self.bot.config.priority_log_channel)
            member = messages[0].author
            timestamp = dt.datetime.now()
            embed = discord.Embed(title="Spam Detected",
                                description=f"{member.mention} has sent multiple identical messages within the last {MESSAGE_AGE} seconds.",
                                color=discord.Color.orange(),
                                timestamp=timestamp)
            avatar = await self.bot.helpers.valid_avatar(member=member)
            embed.set_author(name=member.display_name, icon_url=avatar)
            embed.set_footer(text = f"Member: {member.name} | ID: {member.id}")
            # Avoid repeating message log
            messages = [m async for m in priority_log_channel.history(limit=1)]
            for m in messages:
                if len(m.embeds) == 0 or m.embeds[0].footer.text is None or str(member.id) not in m.embeds[0].footer.text or (str(member.id) in m.embeds[0].footer.text and embed.description != m.embeds[0].description):
                    await priority_log_channel.send(embed=embed)
    

    async def check_excess_dms(self, member: discord.Member) -> None:
        # Experimental feature; may break in the future if Discord API spec changes
        timestamp = dt.datetime.now()
        priority_log_channel = self.bot.get_channel(self.bot.config.priority_log_channel)
        dm_flag = "unusual_dm_activity_until"
        url = f"https://discord.com/api/v10/guilds/{self.bot.config.server_id}/members/{member.id}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bot {self.bot.config.token}'
        }
        try:
            r = requests.get(url=url, headers=headers)
            if r.json()[dm_flag] is not None:
                embed = discord.Embed(title="Excessive DMs Detected",
                                description=f"{member.mention} has been detected by Discord as sending excessive DMs.",
                                color=discord.Color.orange(),
                                timestamp=timestamp)
                avatar = await self.bot.helpers.valid_avatar(member=member)
                embed.set_author(name=member.display_name, icon_url=avatar)
                embed.set_footer(text=f"Member: {member.name} | ID: {member.id}")
                # Avoid repeating message log
                messages = [m async for m in priority_log_channel.history(limit=1)]
                for m in messages:
                    if len(m.embeds) == 0 or m.embeds[0].footer.text is None or str(member.id) not in m.embeds[0].footer.text or (str(member.id) in m.embeds[0].footer.text and embed.description != m.embeds[0].description):
                        await priority_log_channel.send(embed=embed)
        except BaseException as e:
            note = f"**Error occurred when getting excessive DM status for {member.mention}**:\nAttempted to access {url} and returned message: `{r.json()['message']}`"
            embed = discord.Embed(title=None,
                                    description=note,
                                    color=discord.Color.dark_gold(),
                                    timestamp=timestamp
            )
            await priority_log_channel.send(embed=embed)

    # Check roles for guild members who recently joined
    async def add_missing_roles(self, member: discord.Member) -> None:
        role_ids = (role.id for role in member.roles)
        if self.all_role not in role_ids:
            await member.add_roles(RoleSnowflake(id=self.all_role))
        if self.vc_role not in role_ids:
            await member.add_roles(RoleSnowflake(id=self.vc_role))

    # Duplicate welcomes is purely a public-facing cosmetic issue; can deprecate if welcome channel is hidden
    async def remove_duplicate_welcomes(self, message: discord.Message) -> None:
        """Removes duplicate welcome messages."""
        if "just boosted the server!" in message.content:
            return
        else:
            async for m in message.channel.history(limit = 2):
                if m.author.id == message.author.id and m.id != message.id and ("just boosted the server!" not in m.content):
                    await m.delete()

    async def truncate_text(self, text: str) -> None:
        """Checks if input text is greater than maximum embed field length and truncates text if True."""
        MAX_LEN = 1000
        if len(text) > MAX_LEN:
            text = "".join([text[0:(MAX_LEN-10)], " [...]"])
        return text

    # New member joing logging
    async def new_member(self, member: discord.Member) -> None:
        """Sends an embed log for new member join events."""
        timestamp = dt.datetime.now()
        account_age = dt.datetime.now(tz=dt.timezone.utc) - member.created_at
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        default_url = self.bot.helpers.default_url
        embed = discord.Embed(description=f"{member.mention} {member.display_name}\n**Account Age**\n{str(account_age)}",
                            url=default_url,
                            color=discord.Color.green(),
                            timestamp=timestamp)     
        avatar = await self.bot.helpers.valid_avatar(member=member)
        embed.set_author(name="Member Joined", icon_url=avatar)
        embed.set_thumbnail(url=avatar)
        embed.set_footer(text=f"ID: {member.id}")
        await log_channel.send(embed=embed)

    # Log DM replies
    # TODO: add user blocklist to db in case of unwanted responses/abuse
    async def log_dm_reply(self, message: discord.Message) -> None:
        """Logs DMs received by the bot from users."""
        timestamp = dt.datetime.now()
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        member_color = self.bot.helpers.member_color
        default_url = self.bot.helpers.default_url
        embed = discord.Embed(title=None,
                            description=f"**Received DM reply from {message.author.mention}**\n{message.content}",
                            url=default_url,
                            color=member_color,
                            timestamp=timestamp)

        avatar = await self.bot.helpers.valid_avatar(member=message.author)
        embed.set_author(name=message.author, icon_url=avatar)
        embed.set_footer(text=f"Author: {message.author} | ID: {message.author.id}")

        attach = []
        for attachment in message.attachments:
            try: 
                attach.append(await attachment.to_file(use_cached=True))
            except:
                embed.add_field(name="Attachment unable to be sent", value=attachment.filename)

        if len(attach) == 0:
            await log_channel.send(embed=embed)
        else:
            embed.add_field(name="Files included", value="See attachment(s) below")
            await log_channel.send(embed=embed)
            await log_channel.send(files=attach)

    # Listen for new member join and member update events
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self.new_member(member=member)
        await member.add_roles(RoleSnowflake(id=self.all_role))
        if member.public_flags.spammer:
            await asyncio.sleep(1) # Help avoid rate-limiting
            await self.log_spammer(member=member)
        # add VC role after 15 minute delay
        await asyncio.sleep(15*60)
        try:
            await member.add_roles(RoleSnowflake(id=self.vc_role))
        except discord.NotFound:
            msg = f"Attempted to add role to {member.display_name} but member left guild."
            await self.bot.helpers.append_log(function="ext/listeners.py on_member_join", entry=msg)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if before.bot:
            return
        if after.public_flags.spammer:
            await asyncio.sleep(1) # Help avoid rate-limiting
            await self.log_spammer(after)
        await asyncio.sleep(1) # Help avoid rate-limiting
        await self.check_excess_dms(after)  

    
    # Listen for voice state changes
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if self.bot.config.disable_webcams is True and after.self_video is True and before.channel == after.channel:
            vc_channel = after.channel.jump_url
            await member.move_to(channel=None) # effect: kicks from VC
            log_channel = self.bot.get_channel(self.bot.config.log_channel)  
            timestamp = dt.datetime.now()
            message = "This is an automated notification to let you know that webcam use is not permitted on this server. You are welcome to rejoin the voice chat and participate as you were."
            embed = discord.Embed(title="Mod Team Message", description=f"Hello {member.mention},\n\n{message}\n\n ", color=self.bot.helpers.yupil_color)
            embed.set_footer(text="This is a Yupil Bot message on behalf of the Mod Team. If you would like to reach out to a member of the Mod Team, please create a ticket on the server using our ticket system.")
            embed.set_author(name=member.guild.name, icon_url=member.guild.icon)
            try:
                await member.send(embed=embed)
            except:
                embed.set_footer(text="DM unable to be sent.")
                
            embed.title = f"{member.display_name} kicked from {vc_channel}"
            message_log = await log_channel.send(embed=embed)


    # Listen for new message events
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listens for and responds to new messages."""
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        now = dt.datetime.now(dt.timezone.utc)
        if message.author.bot:
            return
        elif message.flags.forwarded and int(message.reference.guild_id) != int(self.bot.config.server_id):
            await log_channel.send(f"Deleting the following forwarded message of external server origin from {message.channel.jump_url}:")
            await message.forward(destination=log_channel)
            await message.delete()
        elif message.channel.id == self.bot.config.welcome_channel:
            await self.remove_duplicate_welcomes(message=message)
        elif isinstance(message.channel, discord.DMChannel):
            await self.log_dm_reply(message=message)

        self.message_cache.append(message)
        await self.detect_spam(messages=self.message_cache, time=now)

    # Run daily checks at EST 12:00/UTC 16:00
    # NOTE: experimental and might also require running fetch_members() instead of calling guild.members
    @tasks.loop(time=dt.time(hour=16, minute=00, tzinfo=dt.timezone.utc))
    async def run_member_checks(self) -> None:
        time_check = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=25)
        guild = self.bot.get_guild(int(self.bot.config.server_id))
        new_members = (member for member in guild.members if member.joined_at > time_check)
        for member in new_members:
            await self.add_missing_roles(member=member)
            await asyncio.sleep(1) # Help avoid rate-limiting

        spammers = (member for member in guild.members if member.public_flags.spammer)
        for member in spammers:
            await self.log_spammer(member=member)
            await asyncio.sleep(1) # Help avoid rate-limiting

    # Log message deletions
    @commands.Cog.listener()
    async def on_raw_message_delete(self, message: discord.RawMessageDeleteEvent) -> None:
        """Listens for and logs non-bot message deletions."""
        timestamp = dt.datetime.now()
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        default_url = self.bot.helpers.default_url
        deletion_color = self.bot.helpers.deletion_color
        attach = []
        try:
            if message.cached_message is not None:
                if message.cached_message.author.bot:
                    return
                user_link = message.cached_message.author.mention
                embed = discord.Embed(title=None,
                                            description=f"**Message sent by {user_link} deleted in {message.cached_message.jump_url}**\n{message.cached_message.content}",
                                            url=default_url,
                                            color=deletion_color,
                                            timestamp=timestamp)
                avatar = await self.bot.helpers.valid_avatar(member=message.cached_message.author)
                embed.set_author(name=message.cached_message.author, icon_url=avatar)
                embed.set_footer(text=f"Author: {message.cached_message.author} | ID: {message.cached_message.author.id}")

                i = 1
                num_attachments = len(message.cached_message.attachments)
                for attachment in message.cached_message.attachments:
                    if attachment.content_type in ("image/png", "image/jpeg", "image/webp", "image/gif", "video/mov", "video/mp4", "video/mpeg", "audio/mpeg", "audio/wav"):
                        try:
                            attach.append(await attachment.to_file(use_cached=True))
                        except BaseException as failure:
                            note = f"Unable to save attachment of type `{attachment.content_type}`, filename: **{attachment.filename}**"
                            embed.add_field(name=f"Attachment {i}/{num_attachments}:", value=note, inline=False)
                    else:
                        note = f"Unable to save attachment of unsupported type `{attachment.content_type}`, filename: **{attachment.filename}**"
                        embed.add_field(name=f"Attachment {i}/{num_attachments}:", value=note, inline=False)
                    i += 1

            else:
                note = "Message not cached, unable to display content."
                channel = self.bot.get_channel(message.channel_id)
                embed = discord.Embed(title=None,
                                            description=f"**Uncached message deleted in {channel.jump_url}**\n{note}",
                                            color=deletion_color,
                                            timestamp=timestamp)
                embed.set_footer(text=f"Message ID: {message.message_id}")

            if len(attach) == 0:
                await log_channel.send(embed=embed)
            else:
                embed.add_field(name="Files included", value="See attachment(s) below")
                await log_channel.send(embed=embed)
                await log_channel.send(files=attach)
        except BaseException as e:
            note = "**Error occurred when logging deleted message**\n"
            embed = discord.Embed(title=None,
                                    description=f"{note+str(e)}",
                                    color=discord.Color.dark_gold(),
                                    timestamp=timestamp
            )
            await log_channel.send(embed=embed)

    # Log message edits
    @commands.Cog.listener()
    async def on_raw_message_edit(self, message: discord.RawMessageUpdateEvent) -> None:
        """Listens for and logs non-bot message updates."""
        timestamp = dt.datetime.now(dt.timezone.utc)
        MAX_AGE = 7 # Don't log edits older than this number, in days
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        default_url = self.bot.helpers.default_url
        edit_color = self.bot.helpers.edit_color

        if (timestamp - message.message.created_at).days > MAX_AGE or message.message.author.bot:
            return
        try:
            if message.cached_message is not None:
                if message.cached_message.clean_content == message.message.clean_content:
                    return
                before = await self.truncate_text(message.cached_message.content)
                after = await self.truncate_text(message.message.content)
                user_link = message.cached_message.author.mention
                embed = discord.Embed(title=None,
                                            description=f"**Message sent by {user_link} edited in {message.cached_message.jump_url}**",
                                            color=edit_color,
                                            timestamp=timestamp)
                if message.cached_message.author.avatar:
                    embed.set_author(name=message.cached_message.author,
                                            icon_url=message.cached_message.author.avatar.url)
                embed.set_footer(text=f"Author: {message.cached_message.author} | ID: {message.cached_message.author.id}")
                embed.add_field(name="Before:", value=before, inline=False)
                embed.add_field(name="After:", value=after, inline=False)
                await log_channel.send(embed=embed)
            else:
                message_channel = await self.bot.fetch_channel(message.channel_id)
                message = await message_channel.fetch_message(message.message_id)
                after = await self.truncate_text(message.content)
                embed = discord.Embed(title=None,
                                            description=f"**Message sent by {message.author.mention} edited in {message.jump_url}**",
                                            color=edit_color,
                                            timestamp=timestamp)
                embed.set_footer(text=f"Author: {message.author} | ID: {message.author.id}")
                embed.add_field(name="Before:", value="`Message uncached`", inline=False)
                embed.add_field(name="After:", value=after, inline=False)
                await log_channel.send(embed=embed)
        except BaseException as e:
            note = "**Error occurred when logging edited message**\n"
            embed = discord.Embed(title=None,
                                    description=f"{note+str(e)}",
                                    color=discord.Color.dark_gold(),
                                    timestamp=timestamp
            )
            await log_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.errors.CommandNotFound):
            msg = f"{ctx.author} attempted to use unregistered command: {ctx.message.content}"
            await self.bot.helpers.append_log(function="ext/listeners.py on_command_error", entry=msg)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ListenCog(bot=bot))