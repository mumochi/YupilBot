from discord import User, Guild, Message, Color
from discord.ext import commands
from discord import app_commands
import configparser
import os

server_id = os.getenv('DISCORD_SERVER_ID')
config = configparser.ConfigParser()
config.read('config.ini')
permitted_role = config[os.getenv('YUPIL_ENV')]['permitted_role']  # Only users with this role can use the commands

# Set embed colors
yupil_color = Color.from_rgb(0, 255, 255)
member_color = Color.from_rgb(252, 192, 246)
deletion_color = Color.from_rgb(255, 71, 15)
edit_color = Color.from_rgb(51, 127, 213)

yupilBot_display_name = None
yupilBot_avatar = None
# Remove duplicate welcome messages
async def remove_duplicate_welcomes(message: Message):
    if "just boosted the server!" in message.content:
        return
    else:
        async for m in message.channel.history(limit = 5):
            if m.author == message.author and m.id != message.id and ("just boosted the server!" not in m.content):
                await m.delete()

# Helper functions for unrestrict command
async def user_channels_on(user: User, guild: Guild):
    """Resets all user-specific channel overrides established by previous restriction"""
    # Iteratively restore normal access to all channels and VCs
    for channel in guild.text_channels:
        try:
            if channel.permissions_for(guild.me).view_channel:
                await channel.set_permissions(user, overwrite = None)
        except:
            print(f"Failed to reveal channel {channel.name}. Skipping")
    for vc in guild.voice_channels:
        try:
            if vc.permissions_for(guild.me).view_channel:
                await vc.set_permissions(user, overwrite = None)
        except:
            print(f"Failed to reveal channel {channel.name}. Skipping")
    for forum in guild.forums:
        try:
            if forum.permissions_for(guild.me).view_channel:
                await forum.set_permissions(user, overwrite = None)
        except:
            print(f"Failed to reveal channel {channel.name}. Skipping")

# Helper functions for restrict command
async def user_channels_off(user: User, guild: Guild):
    """Sets all channel overrides to limit visibility for user"""
    # Iteratively restrict access to every channel and VC
    for channel in guild.text_channels:
        try:
            if channel.permissions_for(guild.me).view_channel:
                perms = channel.overwrites_for(user)
                perms.read_messages = False
                await channel.set_permissions(user, overwrite = perms)
        except:
            print(f"Failed to hide channel {channel.name}. Skipping")
    for vc in guild.voice_channels:
        try:
            if vc.permissions_for(guild.me).view_channel:
                perms_vc = vc.overwrites_for(user)
                perms_vc.view_channel = False
                await vc.set_permissions(user, overwrite = perms_vc)
        except:
            print(f"Failed to hide channel {channel.name}. Skipping")
    for forum in guild.forums:
        try:
            if forum.permissions_for(guild.me).view_channel:
                perms_forum = forum.overwrites_for(user)
                perms_forum.view_channel = False
                await forum.set_permissions(user, overwrite = perms_forum)
        except:
            print(f"Failed to hide channel {channel.name}. Skipping")

def check_if_mod():
    def predicate(self, ctx: commands.Context):
        return ctx.author.id == permitted_role
    return app_commands.check(predicate)


def get_mod_role_id():
    return permitted_role


def get_server_id():
    return server_id


def get_yupil_color():
    return yupil_color


def get_member_color():
    return member_color


def get_deletion_color():
    return deletion_color


def get_edit_color():
    return edit_color


# These will not auto update. Need to add change detection event
def save_YupilBot_display_name(name):
    global yupilBot_display_name
    yupilBot_display_name = name
def get_YupilBot_display_name():
    return yupilBot_display_name


def save_YupilBot_avatar(avatar):
    global yupilBot_avatar
    yupilBot_avatar = avatar


def get_YupilBot_avatar():
    return yupilBot_avatar
