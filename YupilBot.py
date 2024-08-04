import sys
import time
import discord
from discord import app_commands as ac
from discord.ext import commands
import deepl
import configparser
import os
from dotenv import load_dotenv
import datetime
import re

if os.getenv('YUPIL_ENV') != "prod":
    load_dotenv(".env.local")
else:
    load_dotenv(".env")
config = configparser.ConfigParser()
config.read('config.ini')


server_id = os.getenv('DISCORD_SERVER_ID')  # Server ID
permitted_role = config[os.getenv('YUPIL_ENV')]['permitted_role']  # Only users with this role can use the commands

intents = discord.Intents.default() 
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix = '/', intents = intents, max_messages = int(config[os.getenv('YUPIL_ENV')]['cache_size']))
tree = bot.tree

# Set channels
art_channel = int(config[os.getenv('YUPIL_ENV')]['art_channel'])
welcome_channel = int(config[os.getenv('YUPIL_ENV')]['welcome_channel'])

# Set embed colors
yupil_color = discord.Color.from_rgb(0, 255, 255)
deletion_color = discord.Color.from_rgb(255, 71, 15)
edit_color = discord.Color.from_rgb(51, 127, 213)

# DeepL authentication
auth_key = os.getenv('DEEPL_API_TOKEN')

try:
    translator = deepl.Translator(auth_key)
except:
    print("Invalid DeepL key - check current key or generate a new one.")

# Chat command: bot sends a normal chat message to a text channel
@tree.command(
        name = "chat",
        description = "Sends a chat message to the indicated text channel.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    chat_message = "Message to send to text channel",
    channel = "Channel to send the message to",
    as_reply = "Message ID to reply to",
    as_embed = "Send the message as an embed",
    embed_title = "Title for embed",
    image_url = "Image URL for embed",
    embed_url = "URL for embed"
)
async def chat(ctx, chat_message: str, channel: discord.TextChannel, as_reply: str = None,
               as_embed: bool = False, embed_title: str = None, image_url: str = None, embed_url: str = None):
    """Sends a chat message to the indicated text channel."""
    chat_message = chat_message.replace(r'\n', '\n')
    if as_embed:
        chat_embed = discord.Embed(title = embed_title,
                                 description = chat_message,
                                 color = yupil_color,
                                 url = embed_url)
        chat_embed.set_image(url = image_url)
        if as_reply != None:
            try:
                as_reply = await channel.fetch_message(int(as_reply))
                await channel.send(embed = chat_embed, allowed_mentions = discord.AllowedMentions.none(), reference = as_reply)
            except:
                await ctx.response.send_message("Message to reply to not found. Please make sure this is a message ID.", ephemeral = True)
        else:
            await channel.send(embed = chat_embed)
    else:
        if as_reply != None:
            try:
                as_reply = await channel.fetch_message(int(as_reply))
                await channel.send(chat_message, allowed_mentions = discord.AllowedMentions.none(), reference = as_reply)
            except:
                await ctx.response.send_message("Message to reply to not found. Check that this is a message ID.", ephemeral = True)
        else:    
            await channel.send(chat_message)
    await ctx.response.send_message(f"Message sent to {channel.jump_url}", ephemeral = True)

@tree.command(
        name = "kill_me",
        description = "You horrible person. What did the lil guy ever do to you?!",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
        reason = "Motive for the murder."
)
async def kill_me(ctx: discord.ext.commands.Context, reason: str):
    """Sends a chat message to the indicated text channel."""
    log_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
    await log_channel.send(f"{ctx.user.global_name} murdered Yupil Bot for: {reason} <:yuyskull:1160100826975567892>")
    sys.exit(reason)


# DM command: bot sends a DM to a user on the server
@tree.command(
        name = "dm",
        description = "Sends a DM to the indicated user.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    dm_message = "Message to send to user",
    user = "User to send message to"
)
async def dm(ctx, dm_message: str, user: discord.User):
    """Sends a DM to the indicated user."""
    dm_message = dm_message.replace(r'\n', '\n')
    log_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
    guild = await bot.fetch_guild(server_id)
    dm_embed = discord.Embed(title = "Mod Team Message",
                               description = f"Hello {user.mention},\n\n{dm_message}\n\nIf you would like to reach out to the Mod Team, please create a ticket using our ticket system.",
                               color = yupil_color)
    dm_embed.set_footer(text = "This is a Yupil Bot message. The Mod Team is unable to see or respond to further DMs.")
    dm_embed.set_author(name = guild.name,
                        icon_url = guild.icon)
    await user.send(embed = dm_embed)
    message_log = await log_channel.send(f"DM sent to {user.display_name}:", embed = dm_embed)
    await ctx.response.send_message(f"DM sent {message_log.jump_url}", ephemeral = True)

# Restrict command: bot restricts user permissions to view server channels
@tree.command(
        name = "restrict",
        description = "Restricts a user.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to restrict"
)
async def restrict(ctx, user: discord.User):
    """Restricts a user."""
    for channel in ctx.guild.text_channels:
        perms = channel.overwrites_for(user)
        perms.read_messages = False
        await channel.set_permissions(user, overwrite = perms)
    for vc in ctx.guild.voice_channels:
        perms_vc = vc.overwrites_for(user)
        perms_vc.view_channel = False
        await vc.set_permissions(user, overwrite = perms_vc)
    await ctx.response.send_message(f"{user} restricted.")

# Unrestrict command: bot unrestricts user permissions to view server channels
@tree.command(
        name = "unrestrict",
        description = "Unrestricts a user.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to unrestrict"
)
async def unrestrict(ctx, user: discord.User):
    """Unrestricts a user."""
    for channel in ctx.guild.text_channels:
        perms = channel.overwrites_for(user)
        perms.read_messages = None
        await channel.set_permissions(user, overwrite = perms)
    for vc in ctx.guild.voice_channels:
        perms_vc = vc.overwrites_for(user)
        perms_vc.view_channel = None
        await vc.set_permissions(user, overwrite = perms_vc)
    await ctx.response.send_message(f"{user} unrestricted.")

# Translation command using DeepL API
@tree.command(
        name = "translate",
        description = "Translates text to English (EN-US) using the DeepL API.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    text = "Text to translate"
)
async def translate(ctx, text: str):
    """Translates text to English (EN-US) using the DeepL API."""
    tr_text = translator.translate_text(text, target_lang = "EN-US")
    await ctx.response.send_message(f"{text} -> " + str(tr_text) + " (EN-US)")

@bot.event
async def on_message(message: discord.Message):
    if message.channel.id == art_channel:
        await check_art_promo(message = message)
    elif message.channel.id == welcome_channel:
        await remove_duplicate_welcomes(message = message)
    else:
        return


# Remove messages with references to commissions in the embeds (e.g., art account promotion)
async def check_art_promo(message: discord.Message):
    time.sleep(2)  # Need to allow time for the embed to process on Discord's side
    log_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
    block_list = ["comm", "commission", "commision", "comission", "comision", "comisión"]
    permit_list = ["comma", "comme", "commo", "commu"]
    # Skip message if sent by a bot or doesn't contain an embed or sent by a mod
    if (message.author.bot or
        len(message.embeds) == 0 or
        discord.utils.get(message.guild.roles, name = permitted_role) in message.author.roles):
        return
    else:
        remove = False
        # For each embed, search for blocked terms and compare against permitted terms
        # If number blocked > number permitted hits detected, flag message for removal
        # Won't detect edge cases where both blocked > 1 and blocked == permitted
        for embed in message.embeds:
            num_blocked_title = 0
            num_blocked_description = 0
            for word in block_list:
                block_word = re.compile(f".*?{word}.*?")
                num_blocked_title += len(block_word.findall(embed.title.lower()))
                num_blocked_description += len(block_word.findall(embed.description.lower()))
            if num_blocked_title > 0:
                num_permitted_title = 0
                for pword in permit_list:
                    permit_word = re.compile(f".*?{pword}.*?")
                    num_permitted_title += len(permit_word.findall(embed.title.lower()))
                if num_blocked_title > num_permitted_title:
                    remove = True
            if num_blocked_description > 0:
                num_permitted_description = 0
                for pword in permit_list:
                    permit_word = re.compile(f".*?{pword}.*?")
                    num_permitted_description += len(permit_word.findall(embed.description.lower()))
                if num_blocked_description > num_permitted_description:
                    remove = True
    if remove:
        guild = await bot.fetch_guild(server_id)
        send_embed = discord.Embed(title="AutoMod: Blocked Message",
                                   description=f"Hello {message.author.mention},\n\nYou've sent a message that may include references to art commissions. This is a gentle reminder that promotion isn't allowed here, so your message has been automatically deleted. Please feel free to resubmit art as images rather than social links or ensure removal of any commission references.\n\nIf you believe this message was sent to you in error, please create a ticket using our ticket system.\n\nThank you.",
                                   color = yupil_color)
        send_embed.set_footer(text = "This is an automated message. We are unable to see or respond to further DMs.")
        send_embed.set_author(name = guild.name,
                              icon_url = guild.icon)

        await message.author.send(embed = send_embed)
        await log_channel.send(f"DM sent to {message.author.display_name}", embed = send_embed)
        await message.delete()

# Remove duplicate welcome messages
async def remove_duplicate_welcomes(message: discord.Message):
    if "just boosted the server!" in message.content:
        return
    else:
        async for m in message.channel.history(limit = 5):
            if m.author == message.author and m.id != message.id and ("just boosted the server!" not in m.content):
                await m.delete()


@bot.event
async def on_raw_message_delete(message: discord.RawMessageDeleteEvent):
    timestamp = datetime.datetime.now()
    log_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
    attach = []
    try:
        if message.cached_message:
            if message.cached_message.author.bot:
                return
            user_link = await bot.fetch_user(message.cached_message.author.id)
            embedVar = discord.Embed(title = None,
                                         description = f"**Message sent by {user_link.mention} deleted in {message.cached_message.jump_url}**\n{message.cached_message.content}",
                                         color = deletion_color,
                                         timestamp = timestamp)
            if message.cached_message.author.avatar:
                embedVar.set_author(name = message.cached_message.author,
                                        icon_url = message.cached_message.author.avatar.url)
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
            channel = bot.get_channel(message.channel_id)
            embedVar = discord.Embed(title = None,
                                         description = f"**Uncached message deleted in {channel.jump_url}**\n{note}",
                                         color = deletion_color,
                                         timestamp = timestamp)
            embedVar.set_footer(text = f"Message ID: {message.message_id}")

        await log_channel.send(embed = embedVar, files=attach)
    except BaseException as e:
        note = "**Error occurred when logging deleted message**\n"
        embedVar = discord.Embed(title=None,
                                 description=f"{note+str(e)}",
                                 color=discord.Color.dark_gold(),
                                 timestamp= timestamp
        )
        await log_channel.send(embed=embedVar)


@bot.event
async def on_raw_message_edit(message: discord.RawMessageUpdateEvent):
    timestamp = datetime.datetime.now()
    log_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
    try:
        if message.cached_message:
            new_message = await bot.get_channel(message.channel_id).fetch_message(message.data.get('id'))
            before = message.cached_message.content
            after = new_message.content
            if before == after or message.cached_message.author.bot:
                return
            user_link = await bot.fetch_user(message.cached_message.author.id)
            embedVar = discord.Embed(title = None,
                                         description = f"**Message sent by {user_link.mention} edited in {message.cached_message.jump_url}**",
                                         color = edit_color,
                                         timestamp = timestamp)
            if message.cached_message.author.avatar:
                embedVar.set_author(name = message.cached_message.author,
                                        icon_url = message.cached_message.author.avatar.url)
            embedVar.set_footer(text = f"Author: {message.cached_message.author} | ID: {message.cached_message.author.id}")
            embedVar.add_field(name = "Before:", value = before, inline = False)
            embedVar.add_field(name = "After:", value = after, inline = False)

        await log_channel.send(embed = embedVar)
    except BaseException as e:
        note = "**Error occurred when logging edited message**\n"
        embedVar = discord.Embed(title=None,
                                 description=f"{note+str(e)}",
                                 color=discord.Color.dark_gold(),
                                 timestamp= timestamp
        )
        await log_channel.send(embed=embedVar)



# Sync commands
@bot.event
async def on_ready():
    await tree.sync(guild = discord.Object(id = server_id))
    print("Logged in and ready to receive commands.")

# Bot login
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
