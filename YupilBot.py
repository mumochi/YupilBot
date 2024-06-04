import discord
from discord import app_commands as ac
import deepl
import re

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
    name = "get_favorite_emojis",
    description = "Gets the user's most used emoji and reaction",
    guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to get top emoji and reaction for",
)
async def get_favorite_emojis(ctx, user: discord.User):
    emoji_dict = {}
    react_dict = {}
    overall_dict = {}
    await ctx.response.defer(ephemeral=True)
    for channel in ctx.guild.text_channels:
        async for message in channel.history(limit = None):
            if message.author == user:
                found_emojis = re.findall(":.+?:", message.content)
                for emoji in found_emojis:
                    emoji_dict.update({emoji: emoji_dict.get(emoji) + 1 if emoji_dict.get(emoji) else 1})
                    overall_dict.update({emoji: overall_dict.get(emoji) + 1 if overall_dict.get(emoji) else 1})
            elif message.reactions:
                for reaction in message.reactions:
                    users = [user async for user in reaction.users()]
                    if user in users:
                        react_dict.update({reaction: react_dict.get(reaction) + 1 if react_dict.get(reaction) else 1})
                        overall_dict.update({reaction: react_dict.get(reaction) + 1 if react_dict.get(reaction) else 1})

    favorite_emoji = max(emoji_dict, key=lambda x: emoji_dict[x])
    favorite_react = max(react_dict, key=lambda x: react_dict[x])
    favorite_overall = max(overall_dict, key=lambda x: overall_dict[x])
    await ctx.followup.send(f"User favorite emoji: {favorite_emoji} {emoji_dict[favorite_emoji]}, react: {favorite_react} {react_dict[favorite_react]}, overall {favorite_overall} {overall_dict[favorite_overall]}.")

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
