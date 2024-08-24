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
import requests
import typing
from collections import deque

# Set environment and read config file
if os.getenv('YUPIL_ENV') != "prod":
    load_dotenv(".env.local")
else:
    load_dotenv(".env")
config = configparser.ConfigParser()
config.read('config.ini')

# Read config info
server_id = os.getenv('DISCORD_SERVER_ID')  # Server ID
welcome_channel = int(config[os.getenv('YUPIL_ENV')]['welcome_channel'])
helpdesk_channel = int(config[os.getenv('YUPIL_ENV')]['helpdesk_channel'])
permitted_role = config[os.getenv('YUPIL_ENV')]['permitted_role']  # Only users with this role can use the commands
max_messages = int(config[os.getenv('YUPIL_ENV')]['cache_size'])
guild_obj = discord.Object(id = server_id)

# Fetch channels from channel ID
async def get_channels(channel_id: int):
    channel = await bot.fetch_channel(channel_id)
    return(channel)

# Bot client class with one-time setup
class BotClient(commands.Bot):
    def __init__(self, *, command_prefix: str, intents: discord.Intents, max_messages: int):
        super().__init__(command_prefix = command_prefix, intents = intents, max_messages = max_messages)

    async def setup_hook(self):
        self.tree.copy_global_to(guild = guild_obj)
        await self.tree.sync(guild = guild_obj)

        # Get channels
        global log_channel
        global transcript_channel
        global category
        global guild
        log_channel = await get_channels(int(config[os.getenv('YUPIL_ENV')]['log_channel']))
        transcript_channel = await get_channels(int(config[os.getenv('YUPIL_ENV')]['transcript_channel']))
        category = await get_channels(int(config[os.getenv('YUPIL_ENV')]['helpdesk_channel']))
        guild = await self.fetch_guild(server_id)

        # Retrieve ticket button message ID
        if os.path.isfile("buttons_message_id.txt"):
            button_message_id = int(open("buttons_message_id.txt", "r").readline())
            bot.add_view(view = Buttons(timeout = None), message_id = button_message_id)

# Set bot intents and bot configuration
intents = discord.Intents.default() 
intents.message_content = True
intents.members = True
bot = BotClient(command_prefix = '/', intents = intents, max_messages = max_messages)
tree = bot.tree

# Set embed colors
yupil_color = discord.Color.from_rgb(0, 255, 255)
member_color = discord.Color.from_rgb(252, 192, 246)
deletion_color = discord.Color.from_rgb(255, 71, 15)
edit_color = discord.Color.from_rgb(51, 127, 213)

# Default URL for multi-image embeds
default_url = "https://www.twitch.tv/yuy_ix"

# DeepL authentication
auth_key = os.getenv('DEEPL_API_TOKEN')

try:
    translator = deepl.Translator(auth_key)
except:
    print("Invalid DeepL key - check current key or generate a new one.")

# Chat command: bot sends a normal chat message to a text channel
async def valid_message(channel: discord.TextChannel, message_id: str):
    """Checks if a message_id is valid and if the message channel can be found"""
    try:
        message = await channel.fetch_message(int(message_id))
        ctx_message = f"Message sent to {channel.jump_url}"
    except (ValueError, discord.NotFound):
        message = None
        ctx_message = "Message to reply to not found. Check that this is a valid message ID."
    return message, ctx_message

async def valid_url(url: typing.Union[str, None]):
    """Checks if a URL is valid by whether it yields a status code 200"""
    valid = None
    if url is not None:
        valid = False
        # If any errors other than status code 200, supplied str is an invalid URL
        try:
            response = requests.get(url)
            if response.status_code == 200:
                valid = True
        except:
            return valid
    return valid
        

@tree.command(
        name = "chat",
        description = "Sends a chat message to the indicated text channel."
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    chat_message = "Message to send to text channel",
    channel = "Channel to send the message to",
    reply_id = "Message ID to reply to (default: None)",
    as_embed = "Send the message as an embed (default: False)",
    embed_title = "Title for embed (default: None)",
    image_url = "Image URL for embed (default: None)",
    embed_url = "URL for embed, converts embed title to masked link (default: None)",
    embed_footer = "Footer text for embed (default: None)"
)
async def chat(ctx: commands.Context, chat_message: str, channel: discord.TextChannel, reply_id: str = None,
               as_embed: bool = False, embed_title: str = None, image_url: str = None, embed_url: str = None, embed_footer: str = None):
    """Sends a chat message, optionally as an embed, to the indicated text channel."""
    chat_message = chat_message.replace(r'\n', '\n')

    if as_embed:
        # Check for valid embed and image URLs and return early if invalid
        embed_valid = await valid_url(url=embed_url)
        image_valid = await valid_url(url=image_url)
        if embed_valid == False:
            await ctx.response.send_message("Embed URL is not valid.", ephemeral=True)
            return
        elif image_valid == False:
            await ctx.response.send_message("Image URL is not valid.", ephemeral=True)
            return

        embed = discord.Embed(title=embed_title,
                                 description=chat_message,
                                 color=yupil_color,
                                 url=embed_url)
        embed.set_footer(text=embed_footer)
        embed.set_image(url=image_url)

        if reply_id:
            reply_message, ctx_message = await valid_message(channel=channel, message_id=reply_id)
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none(), reference=reply_message)
            await ctx.response.send_message(ctx_message, ephemeral=True)
        else:
            await channel.send(embed=embed)
            await ctx.response.send_message(f"Message sent to {channel.jump_url}", ephemeral=True)
    else:
        if reply_id:
            reply_message, ctx_message = await valid_message(channel=channel, message_id=reply_id)
            await channel.send(chat_message, allowed_mentions=discord.AllowedMentions.none(), reference=reply_message)
            await ctx.response.send_message(ctx_message, ephemeral=True)
        else:    
            await channel.send(chat_message)
            await ctx.response.send_message(f"Message sent to {channel.jump_url}", ephemeral=True)


@tree.command(
        name = "kill_me",
        description = "You horrible person. What did the lil guy ever do to you?!"
)
@ac.checks.has_role(permitted_role)
@ac.describe(
        reason = "Motive for the murder."
)
async def kill_me(ctx: commands.Context, reason: str):
    """Terminates the program and logs the reason."""
    await log_channel.send(f"{ctx.user.global_name} murdered Yupil Bot for: {reason} <:yuyixDeadge:1265738118666125332>")
    sys.exit(reason)


# DM command: bot sends a DM to a user on the server
@tree.command(
        name = "dm",
        description = "Sends a DM to the indicated user."
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    dm_message = "Message to send to user",
    user = "User to send message to"
)
async def dm(ctx: commands.Context, dm_message: str, user: discord.Member):
    """Sends a DM to the indicated user."""
    dm_message = dm_message.replace(r'\n', '\n')
    dm_embed = discord.Embed(title="Mod Team Message",
                               description=f"Hello {user.mention},\n\n{dm_message}\n\n ",
                               color=yupil_color)
    dm_embed.set_footer(text="This is a Yupil Bot message on behalf of the Mod Team. If you would like to reach out to a member of the Mod Team, please create a ticket on the server using our ticket system.")
    dm_embed.set_author(name=guild.name,
                        icon_url=guild.icon)
    await user.send(embed=dm_embed)
    dm_embed.title = f"DM sent to {user.display_name}:"
    message_log = await log_channel.send(embed=dm_embed)
    await ctx.response.send_message(f"DM sent to {user.display_name}. View log: {message_log.jump_url}", ephemeral=True)

# Helper functions for restrict command
async def create_ticket(name: str, guild: discord.Guild):
        """Creates a new ticket channel with appropriate permissions."""
        overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        new_channel = await guild.create_text_channel(name=name,
                                                              category=category,
                                                              overwrites=overwrites)
        return new_channel

# PermissionOverwrite class with user and context-specific permissions
HideChannelPerms = discord.PermissionOverwrite(read_messages=False, view_channel=False)
ShowChannelPerms = discord.PermissionOverwrite(read_messages=True)
ModChannelPerms = discord.PermissionOverwrite(read_messages=True, manage_messages=True)

@tree.command(
        name = "make_ticket",
        description = "Make a ticket channel."
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    ticket_name = "Name of the ticket channel",
    add_member = "Add a member to the newly-created ticket (default: None)"
)
async def make_ticket(ctx: commands.Context, ticket_name: str, add_member: discord.Member = None):
    mod_role = discord.utils.get(ctx.guild.roles, name=permitted_role)
    ticket_channel = await create_ticket(name=ticket_name, guild=ctx.guild)
    await ctx.response.send_message(f"Ticket channel created.", ephemeral=True, delete_after=1)
    await ticket_channel.set_permissions(mod_role, overwrite=ModChannelPerms)
    if add_member:
        await ticket_channel.set_permissions(add_member, overwrite=ShowChannelPerms)


async def channels_off(user: discord.Member, guild: discord.Guild):
    """Sets all channel overrides to restrict visibility for user."""
    # Iteratively restrict access to every server text, voice, and forum channel
    channels = guild.text_channels + guild.voice_channels + guild.forums
    for channel in channels:
        try:
            if channel.permissions_for(guild.me).view_channel:
                await channel.set_permissions(user, overwrite=HideChannelPerms)
        except:
            print(f"No access to {channel}")


# Restrict command: bot restricts user permissions to view server channels
async def valid_avatar(user: discord.Member):
    """Checks if a user has an avatar."""
    avatar_url = None
    if user.avatar is not None:
        avatar_url = user.avatar.url
    return avatar_url


@tree.command(
        name = "restrict",
        description = "Restricts a user from viewing all channels."
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to restrict",
    create_channel = "Whether to create a ticket channel (default: True)",
    send_message = "Whether to send a mod message; sends a default message if no custom_message given (default: True)",
    custom_message = "Custom mod message (default: None)"
)
async def restrict(ctx: commands.Context, user: discord.Member, create_channel: bool = True, send_message: bool = True, custom_message: str = None):
    """Restricts a user from viewing all channels."""
    timestamp = datetime.datetime.now()
    await ctx.response.send_message(f"Restricting {user.display_name}. This may take some time.", ephemeral=True)
    await channels_off(user=user, guild=ctx.guild)

    if create_channel:
        ticket_name = f"ticket-{user.display_name}"
        new_channel = await create_ticket(name=ticket_name.lower(), guild=ctx.guild)
        mod_role = discord.utils.get(ctx.guild.roles, name=permitted_role)
        await new_channel.set_permissions(user, overwrite=ShowChannelPerms)
        await new_channel.set_permissions(mod_role, overwrite=ModChannelPerms)
        
        # Send a default or custom restriction embed message in the newly-created channel
        if send_message:
            mod_message = "We've identified unusual activity on your account. For this reason, we have temporarily restricted your account from viewing or posting in other channels.\n\nTo have this restriction removed, please send us a message here in this channel at your earliest convenience to confirm that this is not an automated bot account. Failure to respond to this message may result in your removal from the server.\n\nThank you for your patience and cooperation."
            
            if custom_message is not None:
                mod_message = custom_message.replace(r'\n', '\n')
            embed = discord.Embed(description=mod_message,
                                          color=yupil_color)
            await new_channel.send(f"Hello, {user.mention}", embed=embed)

    # Send a log of the mod action
    log_embed = discord.Embed(title="Mod Action: Restrict",
                          description=f"{user.mention} has been restricted.",
                          color=discord.Color.red(), 
                          timestamp=timestamp)
    avatar = await valid_avatar(user=user)
    log_embed.set_author(name=user,
                     icon_url=avatar)
    await log_channel.send(embed=log_embed)
    await ctx.delete_original_response()


# Helper functions for unrestrict command
async def channels_on(user: discord.User, guild: discord.Guild):
    """Resets all user-specific channel overrides established by previous restriction."""
    channels = guild.text_channels + guild.voice_channels + guild.forums
    for channel in channels:
        try:
            if channel.permissions_for(guild.me).view_channel:
                await channel.set_permissions(user, overwrite = None)
        except:
            print(f"No access to {channel}")


async def create_transcript(channel: discord.TextChannel, owner: discord.Member = None):
    """Creates two transcripts: one to send in the transcript channel and one to save locally for long-term archival."""
    today = datetime.date.today()
    today_format = f"{today.year}-{'%02d' % today.month}-{'%02d' % today.day}"
    transcript = await chat_exporter.export(channel, tz_info="US/Pacific")
    filename = f"{today_format}-{channel.name}.html"
    transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                   filename=filename)
    transcript_message = await transcript_channel.send(file=transcript_file)

    # If directory doesn't exist, create it. If file already exists, rename rather than overwrite
    if not os.path.isdir("transcripts"):
        os.mkdir("transcripts")
    i = 1
    while os.path.isfile(f"transcripts/{filename}"):
        filename = f"{today_format}-{channel.name}-{i}.html"
        i += 1
    await transcript_message.attachments[0].save(f"transcripts/{filename}")
    embed = discord.Embed(title="Transcript Created",
                          description=None,
                          color=discord.Color.green(),
                          timestamp=datetime.datetime.now())
    if owner is not None:
        avatar = await valid_avatar(user=owner)
        embed.set_author(name=owner.display_name, icon_url=avatar)
        embed.add_field(name="Ticket Owner", value=owner.mention, inline=True)
    embed.add_field(name="Ticket Name", value=channel.name, inline=True)
    embed.add_field(name="Transcript File", value=transcript_message.attachments[0].url, inline=False)
    await transcript_channel.send(embed=embed)
    await transcript_message.delete()


@tree.command(
        name = "save_transcript",
        description = "Saves transcripts for the channel."
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    channel = "Channel to save a transcript for",
    owner = "Member this ticket was made for (default: None)"
)
async def save_transcript(ctx: commands.Context, channel: discord.TextChannel, owner: discord.Member = None):
    """Saves transcripts for the channel."""
    await ctx.response.send_message("Saving transcript.", ephemeral=True, delete_after=1)
    await create_transcript(channel=channel, owner=owner)


# Unrestrict command: bot unrestricts user permissions to view server channels
@tree.command(
        name = "unrestrict",
        description = "Unrestricts a user to restore channel access."
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to unrestrict",
    delete_ticket = "Whether to save a transcript and delete the ticket (default: True)"
)
async def unrestrict(ctx: commands.Context, user: discord.Member, delete_ticket: bool = True):
    """Unrestricts a user to restore channel access."""
    timestamp = datetime.datetime.now()
    await ctx.response.send_message(f"Unrestricting {user.display_name}. This may take some time.", ephemeral=True)
    await channels_on(user=user, guild=ctx.guild)

    # Search for and delete the ticket channel associated with the prior restriction
    if delete_ticket:
        try:
            ticket_name = f"ticket-{user.display_name}"
            ticket_channel = discord.utils.get(ctx.guild.channels, name=ticket_name.lower())
            try:
                await create_transcript(channel=ticket_channel, owner=user)
                await ticket_channel.delete()
            except:
                await ctx.channel.send(f"Unable to create transcript for {ticket_channel.name}.")
        except:
            await ctx.channel.send(f"Ticket channel {ticket_name} not found.")

    # Send a log of the mod action
    embed = discord.Embed(title="Mod Action: Unrestrict",
                          description=f"{user.mention} has been unrestricted.",
                          color=discord.Color.green(), 
                          timestamp=timestamp)
    avatar = await valid_avatar(user=user)
    embed.set_author(name=user,
                     icon_url=avatar)
    await log_channel.send(embed=embed)
    await ctx.delete_original_response()


# Translation command using DeepL API
@tree.command(
        name = "translate",
        description = "Translates text to target language using the DeepL API."
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    text = "Text to translate",
    target_lang = "Target language code supported by DeepL (default: EN-US)"
)
async def translate(ctx: commands.Context, text: str, target_lang: str = "EN-US"):
    """Translates text to target language using the DeepL API."""
    try:
        tr_text = translator.translate_text(text=text, target_lang=target_lang)
        await ctx.response.send_message(f"{text} ({tr_text.detected_source_lang}) -> " + tr_text.text + f" ({target_lang})")
    except:
        await ctx.response.send_message(f"{target_lang} is not a language code supported by DeepL.", ephemeral=True)


# Define modal classes for interactive UI on button clicks
class InfoModal(discord.ui.Modal):
    """On button interaction, displays a modal UI for text input for an Info Ticket."""
    answer = discord.ui.TextInput(label="Please let us know how we can assist you.", 
                                  style=discord.TextStyle.paragraph, 
                                  placeholder="Note: you will not be able to submit images for this ticket type.", 
                                  required=True, min_length=10)
    
    async def on_submit(ctx: commands.Context, interaction: discord.Interaction):
        """Creates a new ticket channel, sends user message, and adds clickable Close Button."""
        await interaction.response.send_message("Your ticket has been submitted. Thank you.", ephemeral=True)
        today = datetime.datetime.today()
        ticket_name = f"{today.year}{'%02d' % today.month}{'%02d' % today.day}-{interaction.user.display_name}"
        new_channel = await create_ticket(name=ticket_name.lower(), guild=interaction.guild)
        mod_role = discord.utils.get(interaction.guild.roles, name=permitted_role)
        await new_channel.set_permissions(mod_role, overwrite=ModChannelPerms)

        message_embed = discord.Embed(description=f"Ticket created by {interaction.user.mention}",
                                      color=member_color)
        avatar = await valid_avatar(user=interaction.user)
        message_embed.set_author(name=interaction.user.display_name,
                                 icon_url=avatar)
        message_embed.add_field(name="Ticket message:", value=ctx.answer)
        await new_channel.send(embed=message_embed, view=CloseButton(timeout=None))

class ModModal(discord.ui.Modal):
    """On button interaction, displays a modal UI for text input for a Mod Ticket."""
    answer = discord.ui.TextInput(label="Please let us know how we can assist you.", 
                                  style=discord.TextStyle.paragraph, 
                                  placeholder="After this initial message, you may submit supporting images.", 
                                  required=True, min_length=10)
    
    async def on_submit(ctx: commands.Context, interaction: discord.Interaction):
        """Creates a new ticket channel, sends user message, and adds clickable Close Button."""
        await interaction.response.send_message("Submitting ticket.", ephemeral=True, delete_after=2)
        today = datetime.datetime.today()
        ticket_name = f"{today.year}{'%02d' % today.month}{'%02d' % today.day}-{interaction.user.display_name}"
        new_channel = await create_ticket(name=ticket_name.lower(), guild=interaction.guild)
        mod_role = discord.utils.get(interaction.guild.roles, name=permitted_role)
        await new_channel.set_permissions(interaction.user, overwrite=ShowChannelPerms)
        await new_channel.set_permissions(mod_role, overwrite=ModChannelPerms)

        # Send Yupil Bot and user message input embeds; include close button
        mod_embed = discord.Embed(title="Automated Message",
                                  description="A member of the Mod Team will respond when they're available. If you have other information to add to your ticket, such as screenshots or other images, feel free to send them now.\n\nThank you for your patience!",
                                  color=yupil_color)
        mod_embed.set_author(name=bot.user.display_name,
                             icon_url=bot.user.avatar.url)
        message_embed = discord.Embed(description=f"Ticket created by {interaction.user.mention}",
                                      color=member_color)
        avatar = await valid_avatar(user=interaction.user)
        message_embed.set_author(name=interaction.user.display_name,
                                 icon_url=avatar)
        message_embed.add_field(name="Initial message:", value=ctx.answer)
        await new_channel.send(f"Welcome, {interaction.user.mention}", embed=mod_embed, view=CloseButton(timeout=None))
        await new_channel.send("\n", embed=message_embed)


# Define button classes for interactive buttons
class Buttons(discord.ui.View):
    """Ticket creation buttons."""
    @discord.ui.button(label="Info Ticket",
                       style=discord.ButtonStyle.gray,
                       custom_id="info01",
                       emoji="📨")  
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Sends the Info Ticket modal UI text prompt."""
        await interaction.response.send_modal(InfoModal(title="Info Ticket"))

    @discord.ui.button(label="Mod Ticket",
                        style=discord.ButtonStyle.gray,
                        custom_id="mod01",
                        emoji="💬") 
    async def mod_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Sends the Mod Ticket modal UI text prompt."""
        await interaction.response.send_modal(ModModal(title="Mod Ticket"))


class FinishButtons(discord.ui.View):
    """Ticket finish buttons."""
    @discord.ui.button(label="Delete Ticket (with transcript)",
                       style=discord.ButtonStyle.gray,
                       emoji="✅")  
    async def delete_transcript_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Saves transcript and then deletes the channel."""
        try:
            await create_transcript(channel=interaction.channel)
            await interaction.channel.delete()
        except:
            interaction.channel.send("Unable to save transcript.")

    @discord.ui.button(label="Delete Ticket (no transcript)",
                       style=discord.ButtonStyle.gray,
                       emoji="⛔")  
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Deletes the channel without saving a transcript."""
        await interaction.channel.delete()


class CloseButton(discord.ui.View):
    """Ticket close button."""
    @discord.ui.button(label="Close Ticket",
                       style=discord.ButtonStyle.gray,
                       emoji="🔒")   
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrites = interaction.channel.overwrites
        mod_role = discord.utils.get(interaction.guild.roles, name=permitted_role)
        await interaction.response.send_message("Closing ticket.", ephemeral=True, delete_after=1)
        for key in overwrites:
            if key not in [mod_role, bot.user, interaction.guild.default_role]:
                await interaction.channel.set_permissions(key, overwrite=None)
        await interaction.message.edit(view=FinishButtons(timeout=None))


@tree.command(
        name = "create_buttons",
        description = "Creates buttons for the ticket system and sends as a message."
)
@ac.checks.has_role(permitted_role)
async def create_buttons(ctx: commands.Context):
    """Creates buttons for the ticket system and sends as a message."""
    await ctx.response.send_message("Creating buttons", ephemeral=True, delete_after=1)
    button_embed = discord.Embed(title="Need help? Create a ticket",
                                 description="To create a ticket, choose a ticket type and click a button below.\n\n1. **Info Ticket**:\n * Text only\n * No response or discussion needed\n * Examples: Sending feedback, notices, and other helpful information\n2. **Mod Ticket**:\n * Text and images supported\n * Talk to a member of the Mod Team\n * Examples: Resolving more complex situations, getting clarifications, etc.",
                                 color=yupil_color)
    button_embed.set_footer(text="Yupil Bot Ticket System",
                            icon_url=bot.user.avatar.url)
    button_message = await ctx.channel.send(embed=button_embed, view=Buttons(timeout=None))
    button_file = open("buttons_message_id.txt", "w")
    button_file.write(str(button_message.id))
    button_file.close()


# Command to add a user to a ticket
@tree.command(
        name = "add_user",
        description = "Adds a user to a ticket."
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to add to a ticket",
    channel = "Ticket channel to add user to",
)
async def add_user(ctx: commands.Context, channel: discord.TextChannel, user: discord.User):
    await channel.set_permissions(user, overwrite=ShowChannelPerms)
    await ctx.response.send_message(f"{user.display_name} added to ticket.", ephemeral=True, delete_after=1)


# Listen for new message events
@bot.event
async def on_message(message: discord.Message):
    """Listens for and responds to new messages."""
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
    """Removes duplicate welcome messages."""
    if "just boosted the server!" in message.content:
        return
    else:
        async for m in message.channel.history(limit = 5):
            if m.author.id == message.author.id and m.id != message.id and ("just boosted the server!" not in m.content):
                await m.delete()


async def valid_attachment(attachment: discord.Attachment):
    """Checks if an attachment has a valid proxy URL by checking for status code 200."""
    response = requests.get(attachment.proxy_url)
    if response.status_code == 200:
        return attachment.proxy_url
    else:
        return None


# Log DM replies
async def log_dm_reply(message: discord.Message):
    """Logs DMs received by the bot from users."""
    timestamp = datetime.datetime.now()
    embed = discord.Embed(title=None,
                          description=f"**Received DM reply from {message.author.mention}**\n{message.content}",
                          url=default_url,
                          color=member_color,
                          timestamp=timestamp)

    avatar = await valid_avatar(user=message.author)
    embed.set_author(name=message.author, icon_url=avatar)
    embed.set_footer(text=f"Author: {message.author} | ID: {message.author.id}")

    embed_list = deque([])
    attach = []
    i = 1
    num_attachments = len(message.attachments)
    for attachment in message.attachments:
        proxy_url = await valid_attachment(attachment=attachment)
        if attachment.content_type in ("image/png", "image/jpeg", "image/webp", "image/gif") and proxy_url is not None:
            if embed.image.url is None:
                embed.set_image(url=attachment.proxy_url)
            else:
                embed_list.append(discord.Embed(url=default_url).set_image(url=attachment.proxy_url))
        elif attachment.content_type in ("video/mov", "video/mp4", "video/mpeg", "audio/mpeg", "audio/wav") and proxy_url is not None:
            attach.append(await attachment.to_file(use_cached=True))
        else:
            note = f"Unable to save attachment of type `{attachment.content_type}`, filename: **{attachment.filename}**"
            embed.add_field(name=f"Attachment {i}/{num_attachments}:", value=note, inline=False)

    if len(embed_list) == 0:
        await log_channel.send(embed=embed) # This isn't strictly necessary but improves single-image display
    else:
        embed_list.appendleft(embed)
        await log_channel.send(embeds=list(embed_list))
    if attach:
        await log_channel.send(files=attach)


# Log message deletions
@bot.event
async def on_raw_message_delete(message: discord.RawMessageDeleteEvent):
    """Listens for and logs non-bot message deletions."""
    timestamp = datetime.datetime.now()
    attach = []
    embed_list = deque([])
    try:
        if message.cached_message is not None:
            if message.cached_message.author.bot:
                return
            user_link = message.cached_message.author.mention
            embedVar = discord.Embed(title=None,
                                         description=f"**Message sent by {user_link} deleted in {message.cached_message.jump_url}**\n{message.cached_message.content}",
                                         url=default_url,
                                         color=deletion_color,
                                         timestamp=timestamp)
            avatar = await valid_avatar(user=message.cached_message.author)
            embedVar.set_author(name=message.cached_message.author, icon_url=avatar)
            embedVar.set_footer(text=f"Author: {message.cached_message.author} | ID: {message.cached_message.author.id}")

            i = 1
            num_attachments = len(message.cached_message.attachments)
            for attachment in message.cached_message.attachments:
                proxy_url = await valid_attachment(attachment=attachment)
                if attachment.content_type in ("image/png", "image/jpeg", "image/webp", "image/gif") and proxy_url is not None:
                    if embedVar.image.url is None:
                        embedVar.set_image(url=proxy_url)
                    else:
                        embed_list.append(discord.Embed(url=default_url).set_image(url=proxy_url))
                elif attachment.content_type in ("video/mov", "video/mp4", "video/mpeg", "audio/mpeg", "audio/wav") and proxy_url is not None:
                    attach.append(await attachment.to_file(use_cached=True))
                else:
                    note = f"Unable to save attachment of type `{attachment.content_type}`, filename: **{attachment.filename}**"
                    embedVar.add_field(name=f"Attachment {i}/{num_attachments}:", value=note, inline=False)
                i += 1

        else:
            note = "Message not cached, unable to display content."
            channel = bot.get_channel(message.channel_id)
            embedVar = discord.Embed(title=None,
                                            description=f"**Uncached message deleted in {channel.jump_url}**\n{note}",
                                            color=deletion_color,
                                            timestamp=timestamp)
            embedVar.set_footer(text=f"Message ID: {message.message_id}")
    
        if len(embed_list) == 0:
            await log_channel.send(embed=embedVar) # This isn't strictly necessary but improves single-image display
        else:
            embed_list.appendleft(embedVar)
            await log_channel.send(embeds=list(embed_list))
        if attach:
            await log_channel.send(files=attach)
    except BaseException as e:
        note = "**Error occurred when logging deleted message**\n"
        embedVar = discord.Embed(title=None,
                                 description=f"{note+str(e)}",
                                 color=discord.Color.dark_gold(),
                                 timestamp = timestamp
        )
        await log_channel.send(embed=embedVar)

async def truncate_text(text: str):
    """Checks if input text is greater than maximum embed field length and truncates text if True."""
    MAX_LEN = 1000
    if len(text) > MAX_LEN:
        text = "".join([text[0:(MAX_LEN-1)], " [...]"])
    return text

# Log message edits
@bot.event
async def on_raw_message_edit(message: discord.RawMessageUpdateEvent):
    """Listens for and logs non-bot message updates."""
    timestamp = datetime.datetime.now()
    try:
        if message.cached_message is not None:
            new_message = await bot.get_channel(message.channel_id).fetch_message(message.data.get('id'))
            before = await truncate_text(message.cached_message.content)
            after = await truncate_text(new_message.content)
            if before == after or message.cached_message.author.bot:
                return
            user_link = message.cached_message.author.mention
            embedVar = discord.Embed(title=None,
                                         description=f"**Message sent by {user_link} edited in {message.cached_message.jump_url}**",
                                         color=edit_color,
                                         timestamp=timestamp)
            if message.cached_message.author.avatar:
                embedVar.set_author(name=message.cached_message.author,
                                        icon_url=message.cached_message.author.avatar.url)
            embedVar.set_footer(text=f"Author: {message.cached_message.author} | ID: {message.cached_message.author.id}")
            embedVar.add_field(name="Before:", value=before, inline=False)
            embedVar.add_field(name="After:", value=after, inline=False)
            await log_channel.send(embed=embedVar)
        else:
            message_channel = await bot.fetch_channel(message.channel_id)
            message = await message_channel.fetch_message(message.message_id)
            after = await truncate_text(message.content)
            if not message.author.bot:
                embedVar = discord.Embed(title=None,
                                        description=f"**Message sent by {message.author.mention} edited in {message.jump_url}**",
                                        color=edit_color,
                                        timestamp=timestamp)
                embedVar.set_footer(text=f"Author: {message.author} | ID: {message.author.id}")
                embedVar.add_field(name="Before:", value="`Message uncached`", inline=False)
                embedVar.add_field(name="After:", value=after, inline=False)
            await log_channel.send(embed=embedVar)
    except BaseException as e:
        note = "**Error occurred when logging edited message**\n"
        embedVar = discord.Embed(title=None,
                                 description=f"{note+str(e)}",
                                 color=discord.Color.dark_gold(),
                                 timestamp=timestamp
        )
        await log_channel.send(embed=embedVar)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

# Bot login
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
