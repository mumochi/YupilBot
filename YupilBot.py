import discord
from discord import app_commands as ac
import deepl
import time

#For WordCloud
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import PIL.Image
import io

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


#WordCloud code
@tree.command(
    name = "word_cloud",
    description = "Generates a word cloud of the user's messages.",
    guild = discord.Object(id = server_id)
)
@ac.checks.has_role(permitted_role)
@ac.describe(
    user = "User to generate word cloud for."
)
async def word_cloud(ctx, user: discord.User):
    PIL.Image.MAX_IMAGE_PIXELS = 1257943060  # Max image size supported to 30720 x 17280 (HHD)
    start_time = time.time()
    word_dict = {}
    await ctx.response.defer(ephemeral=True)
    counter = 0
    skipped_words_dict = {"": True, "\n": True}
    words = ""
    for channel in ctx.guild.text_channels:
        async for message in channel.history(limit=999999999999999999999):
            if message.author == user:
                counter += 1
                words += message.content + " "
                message_split = message.content.split(' ')
                for word in message_split:
                    if word not in skipped_words_dict:
                        if word in word_dict:
                            word_dict.update({word : word_dict.get(word)+1})
                        else:
                            word_dict.update({word : 1})
    for channel in ctx.guild.voice_channels:
        async for message in channel.history(limit=999999999999999999999):
            if message.author == user:
                counter += 1
                message_split = message.content.split(' ')
                words += message.content + " "
                for word in message_split:
                    if word not in skipped_words_dict:
                        if word in word_dict:
                            word_dict.update({word : word_dict.get(word)+1})
                        else:
                            word_dict.update({word : 1})
    sorted_word_dict = dict(sorted(word_dict.items(), key=lambda x:x[1], reverse=True))
    temp_txt_file = io.StringIO(newline='\n')
    for word_pair in sorted_word_dict:
        temp_txt_file.write(f'{word_pair},{sorted_word_dict.get(word_pair)};')
    temp_txt_file.seek(0)
    word_cloud = WordCloud(width=3840, height=2160, max_words=100000000).generate(words)

    end_time = time.time()
    plt.imshow(word_cloud)
    plt.axis("off")
    plt.show()
    await ctx.followup.send(file=discord.File(temp_txt_file, filename="wordfrequencylist.txt") ,content=f'{user.name} has sent {counter} messages. Execution time took {end_time-start_time}')
    # print(temp_txt_file.getvalue())
    PIL.Image.MAX_IMAGE_PIXELS = 178956970  # Return to default image size


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
