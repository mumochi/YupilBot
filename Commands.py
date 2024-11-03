from discord.ext import commands
from discord import User, TextChannel, Embed, AllowedMentions, utils, Color
from discord import app_commands as ac
from Utils import check_if_mod, user_channels_on, user_channels_off, get_mod_role_id, get_server_id, get_yupil_color
import datetime
from TicketTool.TicketComponents import Buttons
from TicketTool.TicketTool import TicketTool
import sys


class Yommands(commands.Cog):
    def __init__(self, bot, translator, log_channel_id):
        self.bot = bot
        self.translator = translator
        self.log_channel_id = log_channel_id

    # Command to add a user to a ticket
    @ac.command(
            name = "add_user",
            description = "Adds a user to a ticket."
    )
    @check_if_mod()
    @ac.describe(
        user = "User to add to a ticket",
        channel = "Ticket channel to add user to",
    )
    async def add_user(self, ctx, channel: TextChannel, user: User):
        new_perms = channel.overwrites_for(user)
        new_perms.read_messages = True
        await channel.set_permissions(user, overwrite = new_perms)
        await ctx.response.send_message(f"{user.display_name} added to ticket.", ephemeral = True, delete_after = 1)

    @ac.command(
            name = "create_buttons",
            description = "Creates buttons for the ticket system."
    )
    @check_if_mod()
    async def create_buttons(self, ctx):
        """Creates buttons for the ticket system."""
        await ctx.response.send_message("Creating buttons", ephemeral = True, delete_after = 1)
        button_embed = Embed(title = "Need help? Create a ticket",
                                     description = "To create a ticket, choose a ticket type and click a button below.\n\n1. **Info Ticket**:\n * Text only\n * No response or discussion needed\n * Examples: Sending feedback, notices, and other helpful information\n2. **Mod Ticket**:\n * Text and images supported\n * Talk to a member of the Mod Team\n * Examples: Resolving more complex situations, getting clarifications, etc.",
                                     color = get_yupil_color())
        button_embed.set_footer(text = "Yupil Bot Ticket System",
                                icon_url = self.bot.user.avatar.url)
        button_message = await ctx.channel.send(embed = button_embed, view = Buttons(timeout = None))
        button_file = open("buttons_message_id.txt", "w")
        button_file.write(str(button_message.id))
        button_file.close()

    # Translation command using DeepL API
    @ac.command(
            name = "translate",
            description = "Translates text to English (EN-US) using the DeepL API.",
    )
    @check_if_mod()
    @ac.describe(
        text = "Text to translate"
    )
    async def translate(self, ctx, text: str):
        """Translates text to English (EN-US) using the DeepL API."""
        if self.translator is not None:
            tr_text = self.translator.translate_text(text, target_lang = "EN-US")
            await ctx.response.send_message(f"{text} -> " + str(tr_text) + " (EN-US)")


    # Unrestrict command: bot unrestricts user permissions to view server channels
    @ac.command(
            name = "unrestrict",
            description = "Unrestricts a user."
    )
    @check_if_mod()
    @ac.describe(
        user = "User to unrestrict",
        delete_ticket = "Whether to save a transcript and delete the ticket (default: True)"
    )
    async def unrestrict(self, ctx, user: User, delete_ticket: bool = True):
        """Unrestricts a user."""
        timestamp = datetime.datetime.now()
        log_channel = self.bot.get_channel(self.log_channel_id)
        await ctx.response.send_message(f"Unrestricting {user.display_name}. This may take some time.", ephemeral = True)
        await user_channels_on(user = user, guild = ctx.guild)

        # Search for and delete the ticket channel associated with the prior restriction
        if delete_ticket:
            try:
                ticket_name = f"ticket-{user.display_name}"
                ticket_channel = utils.get(ctx.guild.channels, name = ticket_name.lower())
                try:
                    await TicketTool.create_transcript(channel = ticket_channel)
                    await ticket_channel.delete()
                except:
                    await ctx.channel.send(f"Unable to create transcript for {ticket_channel.name}.")
            except:
                await ctx.channel.send(f"Ticket channel {ticket_name} not found.")

        # Send a log of the mod action
        embed = Embed(title = "Mod Action: Unrestrict",
                              description = f"{user.mention} has been unrestricted.",
                              color = Color.green(),
                              timestamp = timestamp)
        user_avatar = None
        if user.avatar != None:
            user_avatar = user.avatar.url
        embed.set_author(name = user,
                         icon_url = user_avatar)
        await log_channel.send(embed = embed)
        await ctx.delete_original_response()


    # Restrict command: bot restricts user permissions to view server channels
    @ac.command(
        name="restrict",
        description="Restricts a user."
    )
    @check_if_mod()
    @ac.describe(
        user="User to restrict",
        create_channel="Whether to create a ticket channel (default: True)",
        send_message="Whether to send a mod message, sends a default message if no custom_message given (default: True)",
        custom_message="Custom mod message (default: None)"
    )
    async def restrict(self, ctx, user: User, create_channel: bool = True, send_message: bool = True,
                       custom_message: str = None):
        """Restricts a user."""
        timestamp = datetime.datetime.now()
        log_channel = self.bot.get_channel(self.log_channel_id)
        await ctx.response.send_message(f"Restricting {user.display_name}. This may take some time.", ephemeral=True)
        await user_channels_off(user=user, guild=ctx.guild)

        # Create a new ticket channel and set permissions for both the restricted user and permitted users (mods)
        if create_channel:
            ticket_name = f"ticket-{user.display_name}"
            new_channel = await TicketTool.create_ticket(name=ticket_name.lower(), guild=ctx.guild)
            new_perms = new_channel.overwrites_for(user)
            new_perms.read_messages = True
            mod_role = utils.get(ctx.guild.roles, name=get_mod_role_id())
            mod_perms = new_channel.overwrites_for(mod_role)
            mod_perms.read_messages = True
            mod_perms.manage_messages = True
            await new_channel.set_permissions(user, overwrite=new_perms)
            await new_channel.set_permissions(mod_role, overwrite=mod_perms)

            # Send a default or custom restriction embed message in the newly-created channel
            if send_message:
                mod_message = "We've identified unusual activity on your account. For this reason, we have temporarily restricted your account from viewing or posting in other channels.\n\nTo have this restriction removed, please send us a message here in this channel at your earliest convenience to confirm that this is not an automated bot account. Failure to respond to this message may result in your removal from the server.\n\nThank you for your patience and cooperation."

                if custom_message != None:
                    mod_message = custom_message.replace(r'\n', '\n')

                message_embed = Embed(description=mod_message,
                                              color=get_yupil_color())
                await new_channel.send(f"Hello, {user.mention}", embed=message_embed)

        # Send a log of the mod action
        log_embed = Embed(title="Mod Action: Restrict",
                                  description=f"{user.mention} has been restricted.",
                                  color=Color.red(),
                                  timestamp=timestamp)
        user_avatar = None
        if user.avatar != None:
            user_avatar = user.avatar.url
        log_embed.set_author(name=user,
                             icon_url=user_avatar)
        await log_channel.send(embed=log_embed)
        await ctx.delete_original_response()

    # DM command: bot sends a DM to a user on the server
    @ac.command(
            name = "dm",
            description = "Sends a DM to the indicated user."
    )
    @check_if_mod()
    @ac.describe(
        dm_message = "Message to send to user",
        user = "User to send message to"
    )
    async def dm(self, ctx, dm_message: str, user: User):
        """Sends a DM to the indicated user."""
        dm_message = dm_message.replace(r'\n', '\n')
        log_channel = self.bot.get_channel(self.log_channel_id)
        guild = await self.bot.fetch_guild(get_server_id())
        dm_embed = Embed(title = "Mod Team Message",
                                   description = f"Hello {user.mention},\n\n{dm_message}",
                                   color = get_yupil_color())
        dm_embed.set_footer(text = "This is a Yupil Bot message on behalf of the Mod Team. If you would like to reach out to a member of the Mod Team, please create a ticket on the server using our ticket system.")
        dm_embed.set_author(name = guild.name,
                            icon_url = guild.icon)
        await user.send(embed = dm_embed)
        dm_embed.title = f"DM sent to {user.display_name}:"
        message_log = await log_channel.send(embed = dm_embed)
        await ctx.response.send_message(f"DM sent to {user.display_name}. View log: {message_log.jump_url}", ephemeral = True)


    @ac.command(
            name = "kill_me",
            description = "You horrible person. What did the lil guy ever do to you?!"
    )
    @check_if_mod()
    @ac.describe(
            reason = "Motive for the murder."
    )
    async def kill_me(self, ctx: commands.Context, reason: str):
        """Sends a chat message to the indicated text channel."""
        log_channel = self.bot.get_channel(self.log_channel_id)
        await log_channel.send(f"{ctx.user.global_name} murdered Yupil Bot for: {reason} <:yuyskull:1160100826975567892>")
        sys.exit(reason)


    # Chat command: bot sends a normal chat message to a text channel
    @ac.command(
            name = "chat",
            description = "Sends a chat message to the indicated text channel."
    )
    @check_if_mod()
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
    async def chat(self, ctx, chat_message: str, channel: TextChannel, as_reply: str = None,
                   as_embed: bool = False, embed_title: str = None, image_url: str = None, embed_url: str = None, embed_footer: str = None):
        """Sends a chat message to the indicated text channel."""
        chat_message = chat_message.replace(r'\n', '\n')
        if as_embed:
            chat_embed = Embed(title = embed_title,
                                     description = chat_message,
                                     color = get_yupil_color(),
                                     url = embed_url)
            chat_embed.set_image(url = image_url)
            chat_embed.set_footer(text = embed_footer)
            if as_reply != None:
                try:
                    as_reply = await channel.fetch_message(int(as_reply))
                    await channel.send(embed = chat_embed, allowed_mentions = AllowedMentions.none(), reference = as_reply)
                except:
                    await ctx.response.send_message("Message to reply to not found. Please make sure this is a message ID.", ephemeral = True)
            else:
                await channel.send(embed = chat_embed)
        else:
            if as_reply != None:
                try:
                    as_reply = await channel.fetch_message(int(as_reply))
                    await channel.send(chat_message, allowed_mentions = AllowedMentions.none(), reference = as_reply)
                except:
                    await ctx.response.send_message("Message to reply to not found. Check that this is a message ID.", ephemeral = True)
            else:
                await channel.send(chat_message)
        await ctx.response.send_message(f"Message sent to {channel.jump_url}", ephemeral = True)


async def setup(bot, translator, log_channel_id):
    await bot.add_cog(Yommands(bot=bot, translator=translator, log_channel_id=log_channel_id))