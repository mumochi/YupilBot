# Helpers module to establish additional shared variables and functions

import discord
import requests
from typing import Optional, Tuple

class Helpers:
    def __init__(self) -> None:
        # Embed colors
        self.yupil_color = discord.Color.from_rgb(0, 255, 255)
        self.member_color = discord.Color.from_rgb(252, 192, 246)
        self.deletion_color = discord.Color.from_rgb(255, 71, 15)
        self.edit_color = discord.Color.from_rgb(51, 127, 213)
        # Default URL for multi-image embeds
        self.default_url = "https://www.twitch.tv/yuy_ix"

    async def valid_message(self, channel: discord.TextChannel, message_id: str) -> Tuple[str, str]:
        """Checks if a message_id is valid and if the message channel can be found"""
        try:
            message = await channel.fetch_message(int(message_id))
            ctx_message = f"Message sent to {channel.jump_url}"
        except (ValueError, discord.NotFound):
            message = None
            ctx_message = "Message to reply to not found. Check that this is a valid message ID."
        return message, ctx_message

    async def valid_url(self, url: Optional[str]) -> bool:
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

    async def valid_avatar(self, member: discord.Member) -> bool:
        """Checks if a member has an avatar."""
        avatar_url = None
        if member.avatar is not None:
            avatar_url = member.avatar.url
        return avatar_url