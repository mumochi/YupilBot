from discord import PermissionOverwrite, TextChannel, File, Embed, Color, Guild
from discord.ext import commands
import os
import configparser
import datetime
import chat_exporter
import io


config = configparser.ConfigParser()
config.read('config.ini')

class TicketTool(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_ticket(self, bot: commands.Bot, name: str, helpdesk_cat_id: int, guild: Guild):
        """Creates a new channel"""
        category = await bot.fetch_channel(helpdesk_cat_id)
        # Set default parameters to view the channel for everyone off and on for the bot
        overwrites = {
            guild.default_role: PermissionOverwrite(read_messages=False),
            guild.me: PermissionOverwrite(read_messages=True)
        }
        new_channel = await guild.create_text_channel(name=name,
                                                      category=category,
                                                      overwrites=overwrites)
        return new_channel

    async def create_transcript(self, bot: commands.Bot, channel: TextChannel):
        """Creates two transcripts: one to send in the transcript channel and one to save locally for long-term archival"""
        transcript_channel = bot.get_channel(int(config[os.getenv('YUPIL_ENV')]['transcript_channel']))
        today = datetime.date.today()
        today_format = f"{today.year}-{'%02d' % today.month}-{'%02d' % today.day}"
        transcript = await chat_exporter.export(channel, tz_info = "US/Pacific")
        filename = f"{today_format}-{channel.name}.html"
        transcript_file = File(io.BytesIO(transcript.encode()),
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
        embed = Embed(title = "Transcript Created",
                              description = None,
                              color = Color.green(),
                              timestamp = datetime.datetime.now())
        embed.add_field(name = "Channel", value = channel.name)
        embed.add_field(name = "Transcript file", value = transcript_message.attachments[0].url, inline = False)
        await transcript_message.edit(embed = embed, attachments = [])


async def setup(bot):
    await bot.add_cog(TicketTool(bot=bot))



