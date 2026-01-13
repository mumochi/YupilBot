# Chat and DM functionality module

import discord
from discord import ui
from discord.ext import commands
import discord.app_commands as ac
from typing import Union

class Message(ui.Modal, title="Send Message"):
    answer = ui.TextInput(label="Answer", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Message sent", ephemeral=True)


class CommsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Chat command
    @ac.command(
        name="chat",
        description="Send a message to the indicated channel."
    )
    @ac.describe(
        message="Message to send",
        channel="Send a message to this channel",
        reply_id="Message ID to reply to (optional, default: None)",
        as_embed="Send the message as an embed (optional, default: False)",
        embed_title="Title for embed (optional, default: None)",
        image_url="Image URL for embed (optional, default: None)",
        embed_url="URL for embed, converts embed title to masked link (optional, default: None)",
        embed_footer="Footer text for embed (optional, default: None)"
    )
    async def chat(
        self, interaction: discord.Interaction, message: str, channel: Union[discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.StageChannel],
        reply_id: str=None, as_embed: bool=False, embed_title: str=None, image_url: str=None, embed_url: str=None, embed_footer: str=None) -> None:

        message = message.replace(r'\n', '\n') # Supports sending newline breaks

        if as_embed:
            # Check for valid embed and image URLs and return early if invalid
            for url in (embed_url, image_url):
                url_valid = await self.bot.helpers.valid_url(url=url)
                if url_valid == False:
                    await interaction.response.send_message("URL is not valid.", ephemeral=True)
                    return

            embed = discord.Embed(title=embed_title,
                                    description=message,
                                    color=self.bot.helpers.yupil_color,
                                    url=embed_url)
            embed.set_footer(text=embed_footer)
            embed.set_image(url=image_url)

            if reply_id:
                reply_message, ctx_message = await self.bot.helpers.valid_message(channel=channel, message_id=reply_id, action_type="reply")
                await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none(), reference=reply_message)
                await interaction.response.send_message(ctx_message, ephemeral=True)
            else:
                await channel.send(embed=embed)
                await interaction.response.send_message(f"Message sent to {channel.jump_url}", ephemeral=True)
        else:
            if reply_id:
                reply_message, ctx_message = await self.bot.helpers.valid_message(channel=channel, message_id=reply_id, action_type="reply")
                await channel.send(message, allowed_mentions=discord.AllowedMentions.none(), reference=reply_message)
                await interaction.response.send_message(ctx_message, ephemeral=True)
            else:    
                await channel.send(message)
                await interaction.response.send_message(f"Message sent to {channel.jump_url}", ephemeral=True)
    
    # DM command
    @ac.command(
        name="dm",
        description="Sends a DM to the indicated user."
        )
    @ac.describe(
        message="Message to send to user",
        user="User to send message to"
        )
    async def dm(self, interaction: discord.Interaction, message: str, user: discord.Member) -> None:
        """Sends a DM to the indicated user."""
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        message = message.replace(r'\n', '\n')
        embed = discord.Embed(title="Mod Team Message",
                                description=f"Hello {user.mention},\n\n{message}\n\n ",
                                color=self.bot.helpers.yupil_color)
        embed.set_footer(text="This is a Yupil Bot message on behalf of the Mod Team. If you would like to reach out to a member of the Mod Team, please create a ticket on the server using our ticket system.")
        embed.set_author(name=interaction.guild.name,
                            icon_url=interaction.guild.icon)
        try:
            await user.send(embed=embed)
            embed.title = f"DM sent to {user.display_name}:"
            message_log = await log_channel.send(embed=embed)
            await interaction.response.send_message(f"DM sent to {user.display_name}. View log: {message_log.jump_url}", ephemeral=True)
        except:
            await interaction.response.send_message(f"DM failed to send. {user.display_name} may have DMs turned off.", ephemeral=True)

    # Edit message
    @ac.command(
        name="edit",
        description="Edits a message previously sent by bot."
    )
    @ac.describe(
        channel="Channel of message to be edited",
        message_id="Message ID for the message to edit",
        new_text="Edited message text"
    )
    async def edit(self, interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.StageChannel],message_id: str, new_text: str) -> None:
        """Edits a message previously sent by the bot."""
        edit_message, ctx_message = await self.bot.helpers.valid_message(channel=channel, message_id=message_id, action_type="edit")
        if edit_message is None:
            await interaction.response.send_message(ctx_message, ephemeral=True)
            return
        if edit_message.author.id == self.bot.user.id:
            edit_message = edit_message.replace(r'\n', '\n') # Supports sending newline breaks
            await edit_message.edit(content=new_text)
            await interaction.response.send_message(ctx_message, ephemeral=True)
        else:
            await interaction.response.send_message(f"Unable to edit message; message must be authored by {self.bot.user.name}.", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommsCog(bot=bot))
