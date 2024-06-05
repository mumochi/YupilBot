import discord
from discord import app_commands as ac
import deepl

server_id = # Server ID
permitted_role = "" # Only users with this role can use the commands

intents = discord.Intents.default() 
client = discord.Client(intents = intents)
tree = ac.CommandTree(client) 

# DeepL authentication
try:
    with open("deepl_key.txt") as keyfile:
        auth_key = keyfile.readline()
except FileNotFoundError:
    print("Missing deepl_key.txt; generate an auth key and copy-paste it into deepl_key.txt in the YupilBot.py directory.")

try:
    translator = deepl.Translator(auth_key)
except:
    print("Invalid key - check current key or generate a new one.")

# Chat command: bot sends a normal chat message to a text channel
@tree.command(
        name = "chat",
        description = "Sends a chat message to the indicated text channel.",
        guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    chat_message = "Message to send to text channel",
    channel = "Channel to send the message to"
)
async def chat(ctx, chat_message: str, channel: discord.TextChannel):
    """Sends a chat message to the indicated text channel."""
    await channel.send(chat_message)
    await ctx.response.send_message(f"Message sent to {channel}", delete_after = 1)

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
    await user.send(dm_message)
    await ctx.response.send_message(f"DM sent to {user.id}: " + dm_message)

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

@tree.command(
    name = "get_vc_hours",
    description = "Gets the user's time spent in VC",
    guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to get vc hours for",
    log_channel = "Channel Dyno logs are saved in",
)
async def get_vc_hours(ctx, user: discord.User, log_channel: discord.TextChannel):
    time_in_vc = 0
    last_leave = None
    await ctx.response.defer(ephemeral=True)
    channel_messages = [message async for message in log_channel.history(limit=None)]
    for message in channel_messages:
        for embed in message.embeds:
            if embed.description is not None:
                if str(user.id) in embed.description:
                    if "left voice" in embed.description:
                        if last_leave is None:
                            last_leave = message.created_at
                        else:
                            raise Exception("Leave without join detected")
                    elif "joined voice" in embed.description:
                        if last_leave is not None:
                            time_in_vc += (last_leave - message.created_at).total_seconds()
                            last_leave = None
                        else:
                            raise Exception("Join without leave detected")

    await ctx.followup.send(f"Seconds spent in VC {time_in_vc}")

@tree.command(
    name = "get_nickname_changes",
    description = "Gets the number of the user's nickname changes",
    guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to get nicknames for for",
    log_channel = "Channel Dyno logs are saved in",
)
async def get_nickname_changes(ctx, user: discord.User, log_channel: discord.TextChannel):
    await ctx.response.defer(ephemeral=True)
    name_changes = 0
    channel_messages = [message async for message in log_channel.history(limit=None)]
    for message in channel_messages:
        for embed in message.embeds:
            if embed.description is not None:
                if str(user.id) in embed.description:
                    if "nickname changed" in embed.description:
                        name_changes += 1
    await ctx.followup.send(f"Nickname changes {name_changes}")

# Sync commands
@client.event
async def on_ready():
    await tree.sync(guild = discord.Object(id = server_id))
    print("Logged in and ready to receive commands.")

# Bot login
try:
    with open("token.txt") as tokenfile:
        token = tokenfile.readline()
except FileNotFoundError:
    print("Missing token.txt; generate a token and copy-paste it into token.txt in the YupilBot.py directory.")

try:
    client.run(token)
except:
    print("Invalid token - check current token or generate a new one.")
