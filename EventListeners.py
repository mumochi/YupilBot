from discord.ext import commands
from discord import RawMessageUpdateEvent, Embed, Color, RawMessageDeleteEvent, Message, DMChannel
from Utils import get_edit_color, get_deletion_color, get_member_color, remove_duplicate_welcomes
import datetime


class Yisteners(commands.Cog):
    def __init__(self, bot, log_channel_id, welcome_channel_id):
        self.bot = bot,
        self.log_channel_id = log_channel_id
        self.welcome_channel_id = welcome_channel_id

    # Log message edits
    @commands.Cog.listener()
    async def on_raw_message_edit(self, message: RawMessageUpdateEvent):
        timestamp = datetime.datetime.now()
        log_channel = self.bot.get_channel(self.log_channel_id)
        try:
            if message.cached_message:
                new_message = await self.bot.get_channel(message.channel_id).fetch_message(message.data.get('id'))
                before = message.cached_message.content
                after = new_message.content
                if before == after or message.cached_message.author.bot:
                    return
                user_link = message.cached_message.author.mention
                embedVar = Embed(title = None,
                                             description = f"**Message sent by {user_link} edited in {message.cached_message.jump_url}**",
                                             color = get_edit_color(),
                                             timestamp = timestamp)
                if message.cached_message.author.avatar:
                    embedVar.set_author(name = message.cached_message.author,
                                            icon_url = message.cached_message.author.avatar.url)
                embedVar.set_footer(text = f"Author: {message.cached_message.author} | ID: {message.cached_message.author.id}")
                embedVar.add_field(name = "Before:", value = before, inline = False)
                embedVar.add_field(name = "After:", value = after, inline = False)
            else:
                message_channel = await self.bot.fetch_channel(message.channel_id)
                message = await message_channel.fetch_message(message.message_id)
                embedVar = Embed(title = None,
                                         description = f"**Message sent by {message.author.mention} edited in {message.jump_url}**",
                                         color = get_edit_color(),
                                         timestamp = timestamp)
                embedVar.set_footer(text = f"Author: {message.author} | ID: {message.author.id}")
                embedVar.add_field(name = "Before:", value = "`Message uncached`", inline = False)
                embedVar.add_field(name = "After:", value = message.content, inline = False)

            await log_channel.send(embed = embedVar)
        except BaseException as e:
            note = "**Error occurred when logging edited message**\n"
            embedVar = Embed(title=None,
                                     description=f"{note+str(e)}",
                                     color=Color.dark_gold(),
                                     timestamp= timestamp
            )
            await log_channel.send(embed=embedVar)

    # Log message deletions
    @commands.Cog.listener()
    async def on_raw_message_delete(self, message: RawMessageDeleteEvent):
        timestamp = datetime.datetime.now()
        log_channel = self.bot.get_channel(self.log_channel_id)
        attach = []
        try:
            if message.cached_message:
                if message.cached_message.author.bot:
                    return
                user_link = message.cached_message.author.mention
                embedVar = Embed(title = None,
                                             description = f"**Message sent by {user_link} deleted in {message.cached_message.jump_url}**\n{message.cached_message.content}",
                                             color = get_deletion_color(),
                                             timestamp = timestamp)
                if message.cached_message.author.avatar:
                    embedVar.set_author(name = message.cached_message.author,
                                            icon_url = message.cached_message.author.avatar.url)
                else:
                    embedVar.set_author(name = message.cached_message.author)
                embedVar.set_footer(text = f"Author: {message.cached_message.author} | ID: {message.cached_message.author.id}")

                i = 1
                num_attachments = len(message.cached_message.attachments)
                for attachment in message.cached_message.attachments:
                    if attachment.content_type in ("image/png", "image/jpeg", "image/webp", "image/gif", "video/mov", "video/mp4", "video/mpeg", "audio/mpeg", "audio/wav"):
                        try:
                            attach.append(await attachment.to_file(use_cached=True))
                        except BaseException as failure:
                            note = f"Unable to save attachment of type `{attachment.content_type}`, filename: **{attachment.filename}**"
                            embedVar.add_field(name = f"Attachment {i}/{num_attachments}:", value = note, inline = False)
                    else:
                        note = f"Unable to save attachment of unsupported type `{attachment.content_type}`, filename: **{attachment.filename}**"
                        embedVar.add_field(name = f"Attachment {i}/{num_attachments}:", value = note, inline = False)
                    i += 1

            else:
                note = "Message not cached, unable to display content."
                channel = self.bot.get_channel(message.channel_id)
                embedVar = Embed(title = None,
                                             description = f"**Uncached message deleted in {channel.jump_url}**\n{note}",
                                             color = get_deletion_color(),
                                             timestamp = timestamp)
                embedVar.set_footer(text = f"Message ID: {message.message_id}")

            if len(attach) == 0:
                await log_channel.send(embed = embedVar)
            else:
                embedVar.add_field(name = "Files included", value = "See attachment(s) below")
                await log_channel.send(embed = embedVar)
                await log_channel.send(files = attach)
        except BaseException as e:
            note = "**Error occurred when logging deleted message**\n"
            embedVar = Embed(title=None,
                                     description=f"{note+str(e)}",
                                     color=Color.dark_gold(),
                                     timestamp= timestamp
            )
            await log_channel.send(embed=embedVar)

    # Log DM replies
    async def log_dm_reply(self, message: Message):
        timestamp = datetime.datetime.now()
        log_channel = self.bot.get_channel(self.log_channel_id)
        embed = Embed(title = "DM Reply",
                              description = f"**Received DM reply from {message.author.mention}**\n{message.content}",
                              color = get_member_color(),
                              timestamp = timestamp)

        if message.author.avatar:
            embed.set_author(name = message.author,
                             icon_url = message.author.avatar.url)
        else:
            embed.set_author(name = message.author)
        embed.set_footer(text = f"Author: {message.author} | ID: {message.author.id}")

        attach = []
        for attachment in message.attachments:
            try:
                attach.append(await attachment.to_file(use_cached = True))
            except:
                embed.add_field(name = "Attachment unable to be sent", value = attachment.filename)

        if len(attach) == 0:
            await log_channel.send(embed = embed)
        else:
            embed.add_field(name = "Files included", value = "See attachment(s) below")
            await log_channel.send(embed = embed)
            await log_channel.send(files = attach)

    # Listen for new message events
    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        elif message.channel.id == self.welcome_channel_id:
            await remove_duplicate_welcomes(message = message)
        elif isinstance(message.channel, DMChannel):
            await self.log_dm_reply(message = message)
        else:
            return


async def setup(bot, log_channel_id, welcome_channel_id):
    await bot.add_cog(Yisteners(bot=bot, log_channel_id=log_channel_id, welcome_channel_id=welcome_channel_id))
