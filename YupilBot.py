import sys
import discord
from discord import app_commands as ac
from discord.ext import commands
import deepl
import configparser
import os
from dotenv import load_dotenv
import datetime
import chat_exporter
import io

# Set environment and read config file
if os.getenv('YUPIL_ENV') != "prod":
    load_dotenv(".env.local")
else:
    load_dotenv(".env")
config = configparser.ConfigParser()
config.read('config.ini')

server_id = os.getenv('DISCORD_SERVER_ID')  # Server ID
permitted_role = config[os.getenv('YUPIL_ENV')]['permitted_role']  # Only users with this role can use the commands

# Set bot intents and bot configuration
intents = discord.Intents.default() 
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix = '/', intents = intents, max_messages = int(config[os.getenv('YUPIL_ENV')]['cache_size']))
tree = bot.tree

# Set channels
welcome_channel = int(config[os.getenv('YUPIL_ENV')]['welcome_channel'])
helpdesk_channel = int(config[os.getenv('YUPIL_ENV')]['helpdesk_channel'])

# Set embed colors
yupil_color = discord.Color.from_rgb(0, 255, 255)
member_color = discord.Color.from_rgb(252, 192, 246)
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
    embed_url = "URL for embed",
    embed_footer = "Footer for embed"
)
async def chat(ctx, chat_message: str, channel: discord.TextChannel, as_reply: str = None,
               as_embed: bool = False, embed_title: str = None, image_url: str = None, embed_url: str = None, embed_footer: str = None):
    """Sends a chat message to the indicated text channel."""
    chat_message = chat_message.replace(r'\n', '\n')
    if as_embed:
        chat_embed = discord.Embed(title = embed_title,
                                 description = chat_message,
                                 color = yupil_color,
                                 url = embed_url)
        chat_embed.set_image(url = image_url)
        chat_embed.set_footer(text = embed_footer)
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
                               description = f"Hello {user.mention},\n\n{dm_message}",
                               color = yupil_color)
    dm_embed.set_footer(text = "This is a Yupil Bot message on behalf of the Mod Team. If you would like to reach out to a member of the Mod Team, please create a ticket on the server using our ticket system.")
    dm_embed.set_author(name = guild.name,
                        icon_url = guild.icon)
    await user.send(embed = dm_embed)
    dm_embed.title = f"DM sent to {user.display_name}:"
    message_log = await log_channel.send(embed = dm_embed)
    await ctx.response.send_message(f"DM sent to {user.display_name}. View log: {message_log.jump_url}", ephemeral = True)

# Helper functions for restrict command
async def create_ticket(name: str, guild: discord.Guild):
        """Creates a new channel"""
        category = await bot.fetch_channel(helpdesk_channel)
        # Set default parameters to view the channel for everyone off and on for the bot
        overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages = False),
        guild.me: discord.PermissionOverwrite(read_messages = True)
        }
        new_channel = await guild.create_text_channel(name = name,
                                                              category = category,
                                                              overwrites = overwrites)
        return new_channel

async def user_channels_off(user: discord.User, guild: discord.Guild):
    """Sets all channel overrides to limit visibility for user"""
    # Iteratively restrict access to every channel and VC
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).view_channel:
            perms = channel.overwrites_for(user)
            perms.read_messages = False
            await channel.set_permissions(user, overwrite = perms)
    for vc in guild.voice_channels:
        if vc.permissions_for(guild.me).view_channel:
            perms_vc = vc.overwrites_for(user)
            perms_vc.view_channel = False
            await vc.set_permissions(user, overwrite = perms_vc)
    for forum in guild.forums:
        if forum.permissions_for(guild.me).view_channel:
            perms_forum = forum.overwrites_for(user)
            perms_forum.view_channel = False
            await forum.set_permissions(user, overwrite = perms_forum)

# Restrict command: bot restricts user permissions to view server channels
@tree.command(
        name = "restrict",
        description = "Restricts a user.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to restrict",
    create_channel = "Whether to create a ticket channel (default: True)",
    send_message = "Whether to send a mod message, sends a default message if no custom_message given (default: True)",
    custom_message = "Custom mod message (default: None)"
)
async def restrict(ctx, user: discord.User, create_channel: bool = True, send_message: bool = True, custom_message: str = None):
    """Restricts a user."""
    timestamp = datetime.datetime.now()
    log_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
    await ctx.response.send_message(f"Restricting {user.display_name}. This may take some time.", ephemeral = True)
    await user_channels_off(user = user, guild = ctx.guild)

    # Create a new ticket channel and set permissions for both the restricted user and permitted users (mods)
    if create_channel:
        ticket_name = f"ticket-{user.display_name}"
        new_channel = await create_ticket(name = ticket_name.lower(), guild = ctx.guild)
        new_perms = new_channel.overwrites_for(user)
        new_perms.read_messages = True
        mod_role = discord.utils.get(ctx.guild.roles, name = permitted_role)
        mod_perms = new_channel.overwrites_for(mod_role)
        mod_perms.read_messages = True
        mod_perms.manage_messages = True
        await new_channel.set_permissions(user, overwrite = new_perms)
        await new_channel.set_permissions(mod_role, overwrite = mod_perms)
        
        # Send a default or custom restriction embed message in the newly-created channel
        if send_message:
            mod_message = "We've identified unusual activity on your account. For this reason, we have temporarily restricted your account from viewing or posting in other channels.\n\nTo have this restriction removed, please send us a message here in this channel at your earliest convenience to confirm that this is not an automated bot account. Failure to respond to this message may result in your removal from the server.\n\nThank you for your patience and cooperation."
            
            if custom_message != None:
                mod_message = custom_message.replace(r'\n', '\n')

            message_embed = discord.Embed(description = mod_message,
                                          color = yupil_color)
            await new_channel.send(f"Hello, {user.mention}", embed = message_embed)

    # Send a log of the mod action
    log_embed = discord.Embed(title = "Mod Action: Restrict",
                          description = f"{user.mention} has been restricted.",
                          color = discord.Color.red(), 
                          timestamp = timestamp)
    user_avatar = None
    if user.avatar != None:
        user_avatar = user.avatar.url
    log_embed.set_author(name = user,
                     icon_url = user_avatar)
    await log_channel.send(embed = log_embed)
    await ctx.delete_original_response()

# Helper functions for unrestrict command
async def user_channels_on(user: discord.User, guild: discord.Guild):
    """Resets all user-specific channel overrides established by previous restriction"""
    # Iteratively restore normal access to all channels and VCs
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).view_channel:
            await channel.set_permissions(user, overwrite = None)
    for vc in guild.voice_channels:
        if vc.permissions_for(guild.me).view_channel:
            await vc.set_permissions(user, overwrite = None)
    for forum in guild.forums:
        if forum.permissions_for(guild.me).view_channel:
            await forum.set_permissions(user, overwrite = None)      

async def create_transcript(channel: discord.TextChannel):
    """Creates two transcripts: one to send in the transcript channel and one to save locally for long-term archival"""
    transcript_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['transcript_channel']))
    today = datetime.date.today()
    today_format = f"{today.year}-{'%02d' % today.month}-{'%02d' % today.day}"
    transcript = await chat_exporter.export(channel, tz_info = "US/Pacific")
    filename = f"{today_format}-{channel.name}.html"
    transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                   filename = filename)
    transcript_message = await transcript_channel.send(file = transcript_file)
    # If directory doesn't exist, create it
    if not os.path.isdir("transcripts"):
        os.mkdir("transcripts")
    # If file already exists, rename rather than overwrite
    i = 1
    while os.path.isfile(f"transcripts/{filename}"):
        filename = f"{today_format}-{channel.name}-{i}.html"
        i += 1
    await transcript_message.attachments[0].save(f"transcripts/{filename}")
    embed = discord.Embed(title = "Transcript Created",
                          description = None,
                          color = discord.Color.green(),
                          timestamp = datetime.datetime.now())
    embed.add_field(name = "Channel", value = channel.name)
    embed.add_field(name = "Transcript file", value = transcript_message.attachments[0].url, inline = False)
    await transcript_message.edit(embed = embed, attachments = [])


# Unrestrict command: bot unrestricts user permissions to view server channels
@tree.command(
        name = "unrestrict",
        description = "Unrestricts a user.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to unrestrict",
    delete_ticket = "Whether to save a transcript and delete the ticket (default: True)"
)
async def unrestrict(ctx, user: discord.User, delete_ticket: bool = True):
    """Unrestricts a user."""
    timestamp = datetime.datetime.now()
    log_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
    await ctx.response.send_message(f"Unrestricting {user.display_name}. This may take some time.", ephemeral = True)
    await user_channels_on(user = user, guild = ctx.guild)

    # Search for and delete the ticket channel associated with the prior restriction
    if delete_ticket:
        try:
            ticket_name = f"ticket-{user.display_name}"
            ticket_channel = discord.utils.get(ctx.guild.channels, name = ticket_name.lower())
            try:
                await create_transcript(channel = ticket_channel)
                await ticket_channel.delete()
            except:
                await ctx.channel.send(f"Unable to create transcript for {ticket_channel.name}.")
        except:
            await ctx.channel.send(f"Ticket channel {ticket_name} not found.")

    # Send a log of the mod action
    embed = discord.Embed(title = "Mod Action: Unrestrict",
                          description = f"{user.mention} has been unrestricted.",
                          color = discord.Color.green(), 
                          timestamp = timestamp)
    user_avatar = None
    if user.avatar != None:
        user_avatar = user.avatar.url
    embed.set_author(name = user,
                     icon_url = user_avatar)
    await log_channel.send(embed = embed)
    await ctx.delete_original_response()

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

# Define modal classes for interactive UI on button clicks
class InfoModal(discord.ui.Modal):
    answer = discord.ui.TextInput(label = "Please let us know how we can assist you.", 
                                  style = discord.TextStyle.paragraph, 
                                  placeholder = "Note: you will not be able to submit images for this ticket type.", 
                                  required = True, min_length = 10)
    
    async def on_submit(ctx, interaction: discord.Interaction):
        await interaction.response.send_message("Your ticket has been submitted. Thank you.", ephemeral = True)
        # Create new ticket and set permissions
        today = datetime.datetime.today()
        ticket_name = f"{today.year}{'%02d' % today.month}{'%02d' % today.day}-{interaction.user.display_name}"
        new_channel = await create_ticket(name = ticket_name.lower(), guild = interaction.guild)
        mod_role = discord.utils.get(interaction.guild.roles, name = permitted_role)
        mod_perms = new_channel.overwrites_for(mod_role)
        mod_perms.read_messages = True
        mod_perms.manage_messages = True
        await new_channel.set_permissions(mod_role, overwrite = mod_perms)

        # Send user input message and include close button
        message_embed = discord.Embed(description = f"Ticket created by {interaction.user.mention}",
                                      color = member_color)
        user_avatar = None
        if interaction.user.avatar != None:
            user_avatar = interaction.user.avatar.url
        message_embed.set_author(name = interaction.user.display_name,
                                 icon_url = user_avatar)
        message_embed.add_field(name = "Ticket message:", value = ctx.answer)
        await new_channel.send(embed = message_embed, view = CloseButton(timeout = None))

class ModModal(discord.ui.Modal):
    answer = discord.ui.TextInput(label = "Please let us know how we can assist you.", 
                                  style = discord.TextStyle.paragraph, 
                                  placeholder = "After this initial message, you may submit supporting images.", 
                                  required = True, min_length = 10)
    
    async def on_submit(ctx, interaction: discord.Interaction):
        await interaction.response.send_message("Submitting ticket.", ephemeral = True, delete_after = 2)
        # Create new ticket and set permissions
        today = datetime.datetime.today()
        ticket_name = f"{today.year}{'%02d' % today.month}{'%02d' % today.day}-{interaction.user.display_name}"
        new_channel = await create_ticket(name = ticket_name.lower(), guild = interaction.guild)
        new_perms = new_channel.overwrites_for(interaction.user)
        new_perms.read_messages = True
        mod_role = discord.utils.get(interaction.guild.roles, name = permitted_role)
        mod_perms = new_channel.overwrites_for(mod_role)
        mod_perms.read_messages = True
        mod_perms.manage_messages = True
        await new_channel.set_permissions(interaction.user, overwrite = new_perms)
        await new_channel.set_permissions(mod_role, overwrite = mod_perms)

        # Send Yupil Bot and user message input embeds; include close button
        mod_embed = discord.Embed(title = "Automated Message",
                                  description = "A member of the Mod Team will respond when they're available. If you have other information to add to your ticket, such as screenshots or other images, feel free to send them now.\n\nThank you for your patience!",
                                  color = yupil_color)
        mod_embed.set_author(name = bot.user.display_name,
                             icon_url = bot.user.avatar.url)
        message_embed = discord.Embed(description = f"Ticket created by {interaction.user.mention}",
                                      color = member_color)
        user_avatar = None
        if interaction.user.avatar != None:
            user_avatar = interaction.user.avatar.url
        message_embed.set_author(name = interaction.user.display_name,
                                 icon_url = user_avatar)
        message_embed.add_field(name = "Initial message:", value = ctx.answer)
        await new_channel.send(f"Welcome, {interaction.user.mention}", embed = mod_embed, view = CloseButton(timeout = None))
        await new_channel.send("\n", embed = message_embed)

# Define button classes for interactive buttons
class Buttons(discord.ui.View):
    @discord.ui.button(label = "Info Ticket",
                       style = discord.ButtonStyle.gray,
                       custom_id = "info01",
                       emoji = "📨")
    
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InfoModal(title = "Info Ticket"))

    @discord.ui.button(label = "Mod Ticket",
                        style = discord.ButtonStyle.gray,
                        custom_id = "mod01",
                        emoji = "💬")
    
    async def mod_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModModal(title = "Mod Ticket"))

class FinishButtons(discord.ui.View):
    @discord.ui.button(label = "Delete Ticket (with transcript)",
                       style = discord.ButtonStyle.gray,
                       emoji = "✅")
    
    async def delete_transcript_button(self, interaction: discord.Interaction, button: discord.ui.Button): 
        try:
            await create_transcript(channel = interaction.channel)
            await interaction.channel.delete()
        except:
            interaction.channel.send("Unable to save transcript.")

    @discord.ui.button(label = "Delete Ticket (no transcript)",
                       style = discord.ButtonStyle.gray,
                       emoji = "⛔")
    
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()



class CloseButton(discord.ui.View):
    @discord.ui.button(label = "Close Ticket",
                       style = discord.ButtonStyle.gray,
                       emoji = "🔒")
    
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrites = interaction.channel.overwrites
        mod_role = discord.utils.get(interaction.guild.roles, name = permitted_role)
        await interaction.response.send_message("Closing ticket.", ephemeral = True, delete_after = 1)
        for key in overwrites:
            if key not in [mod_role, bot.user, interaction.guild.default_role]:
                await interaction.channel.set_permissions(key, overwrite = None)
        await interaction.message.edit(view = FinishButtons(timeout = None))

@tree.command(
        name = "create_buttons",
        description = "Creates buttons for the ticket system.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
async def create_buttons(ctx):
    """Creates buttons for the ticket system."""
    await ctx.response.send_message("Creating buttons", ephemeral = True, delete_after = 1)
    button_embed = discord.Embed(title = "Need help? Create a ticket",
                                 description = "To create a ticket, choose a ticket type and click a button below.\n\n1. **Info Ticket**:\n * Text only\n * No response or discussion needed\n * Examples: Sending feedback, notices, and other helpful information\n2. **Mod Ticket**:\n * Text and images supported\n * Talk to a member of the Mod Team\n * Examples: Resolving more complex situations, getting clarifications, etc.",
                                 color = yupil_color)
    button_embed.set_footer(text = "Yupil Bot Ticket System",
                            icon_url = bot.user.avatar.url)
    button_message = await ctx.channel.send(embed = button_embed, view = Buttons(timeout = None))
    button_file = open("buttons_message_id.txt", "w")
    button_file.write(str(button_message.id))
    button_file.close()

# Command to add a user to a ticket
@tree.command(
        name = "add_user",
        description = "Adds a user to a ticket.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to add to a ticket",
    channel = "Ticket channel to add user to",
)
async def add_user(ctx, channel: discord.TextChannel, user: discord.User):
    new_perms = channel.overwrites_for(user)
    new_perms.read_messages = True
    await channel.set_permissions(user, overwrite = new_perms)
    await ctx.response.send_message(f"{user.display_name} added to ticket.", ephemeral = True, delete_after = 1)

# Listen for new message events
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    elif message.channel.id == welcome_channel:
        await remove_duplicate_welcomes(message = message)
    elif isinstance(message.channel, discord.DMChannel):
        await log_dm_reply(message = message)
    else:
        return

# Remove duplicate welcome messages
async def remove_duplicate_welcomes(message: discord.Message):
    if "just boosted the server!" in message.content:
        return
    else:
        async for m in message.channel.history(limit = 5):
            if m.author == message.author and m.id != message.id and ("just boosted the server!" not in m.content):
                await m.delete()

# Log DM replies
async def log_dm_reply(message: discord.Message):
    timestamp = datetime.datetime.now()
    log_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
    embed = discord.Embed(title = "DM Reply",
                          description = f"**Received DM reply from {message.author.mention}**\n{message.content}",
                          color = member_color,
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

# Log message deletions
@bot.event
async def on_raw_message_delete(message: discord.RawMessageDeleteEvent):
    timestamp = datetime.datetime.now()
    log_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
    attach = []
    try:
        if message.cached_message:
            if message.cached_message.author.bot:
                return
            user_link = message.cached_message.author.mention
            embedVar = discord.Embed(title = None,
                                         description = f"**Message sent by {user_link} deleted in {message.cached_message.jump_url}**\n{message.cached_message.content}",
                                         color = deletion_color,
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
            channel = bot.get_channel(message.channel_id)
            embedVar = discord.Embed(title = None,
                                         description = f"**Uncached message deleted in {channel.jump_url}**\n{note}",
                                         color = deletion_color,
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
        embedVar = discord.Embed(title=None,
                                 description=f"{note+str(e)}",
                                 color=discord.Color.dark_gold(),
                                 timestamp= timestamp
        )
        await log_channel.send(embed=embedVar)

# Log message edits
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
            user_link = message.cached_message.author.mention
            embedVar = discord.Embed(title = None,
                                         description = f"**Message sent by {user_link} edited in {message.cached_message.jump_url}**",
                                         color = edit_color,
                                         timestamp = timestamp)
            if message.cached_message.author.avatar:
                embedVar.set_author(name = message.cached_message.author,
                                        icon_url = message.cached_message.author.avatar.url)
            embedVar.set_footer(text = f"Author: {message.cached_message.author} | ID: {message.cached_message.author.id}")
            embedVar.add_field(name = "Before:", value = before, inline = False)
            embedVar.add_field(name = "After:", value = after, inline = False)
        else:
            message_channel = await bot.fetch_channel(message.channel_id)
            message = await message_channel.fetch_message(message.message_id)
            embedVar = discord.Embed(title = None,
                                     description = f"**Message sent by {message.author.mention} edited in {message.jump_url}**",
                                     color = edit_color,
                                     timestamp = timestamp)
            embedVar.set_footer(text = f"Author: {message.author} | ID: {message.author.id}")
            embedVar.add_field(name = "Before:", value = "`Message uncached`", inline = False)
            embedVar.add_field(name = "After:", value = message.content, inline = False)

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
    # Retrieve ticket button message ID
    if os.path.isfile("buttons_message_id.txt"):
        button_message_id = int(open("buttons_message_id.txt", "r").readline())
        bot.add_view(view = Buttons(timeout = None), message_id = button_message_id)
    print("Logged in and ready to receive commands.")

# Bot login
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
