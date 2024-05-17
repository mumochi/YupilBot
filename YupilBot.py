import discord
from discord import app_commands as ac

server_id =  # Server ID for Yuy and the Yupils
permitted_role = "" # Only users with this role can use the commands

intents = discord.Intents.default() 
client = discord.Client(intents = intents)
tree = ac.CommandTree(client) 

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
