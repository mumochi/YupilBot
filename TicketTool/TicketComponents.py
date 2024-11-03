from discord import ui, ButtonStyle, Interaction, utils, TextStyle, Embed
from discord.ext import commands
from TicketTool import TicketTool
from Utils import get_yupil_color, get_member_color, get_mod_role_id, get_YupilBot_avatar, get_YupilBot_display_name
import datetime
class CloseButton(ui.View):
    @ui.button(label="Close Ticket",
                       style=ButtonStyle.gray,
                       emoji="🔒")
    async def close_button(self, bot: commands.Bot, interaction: Interaction, button: ui.Button, mod_role_name: str):
        overwrites = interaction.channel.overwrites
        mod_role = utils.get(interaction.guild.roles, name=mod_role_name)
        await interaction.response.send_message("Closing ticket.", ephemeral=True, delete_after=1)
        for key in overwrites:
            if key not in [mod_role, bot.user, interaction.guild.default_role]:
                await interaction.channel.set_permissions(key, overwrite=None)
        await interaction.message.edit(view=FinishButtons(timeout=None))


class FinishButtons(ui.View):
    @ui.button(label="Delete Ticket (with transcript)",
                       style=ButtonStyle.gray,
                       emoji="✅")
    async def delete_transcript_button(self, interaction: Interaction, button: ui.Button):
        try:
            await TicketTool.create_transcript(channel=interaction.channel)
            await interaction.channel.delete()
        except:
            await interaction.channel.send("Unable to save transcript.")

    @ui.button(label="Delete Ticket (no transcript)",
                       style=ButtonStyle.gray,
                       emoji="⛔")
    async def delete_button(self, interaction: Interaction, button: ui.Button):
        await interaction.channel.delete()


# Define button classes for interactive buttons
class Buttons(ui.View):
    @ui.button(label="Info Ticket",
                       style=ButtonStyle.gray,
                       custom_id="info01",
                       emoji="📨")
    async def info_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(InfoModal(title="Info Ticket"))

    @ui.button(label="Mod Ticket",
                       style=ButtonStyle.gray,
                       custom_id="mod01",
                       emoji="💬")
    async def mod_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(ModModal(title="Mod Ticket"))


class InfoModal(ui.Modal):
    answer = ui.TextInput(label="Please let us know how we can assist you.",
                                  style=TextStyle.paragraph,
                                  placeholder="Note: you will not be able to submit images for this ticket type.",
                                  required=True, min_length=10)

    async def on_submit(ctx, interaction: Interaction):
        await interaction.response.send_message("Your ticket has been submitted. Thank you.", ephemeral=True)
        # Create new ticket and set permissions
        today = datetime.datetime.today()
        ticket_name = f"{today.year}{'%02d' % today.month}{'%02d' % today.day}-{interaction.user.display_name}"
        new_channel = await TicketTool.create_ticket(name=ticket_name.lower(), guild=interaction.guild)
        mod_role = utils.get(interaction.guild.roles, name=get_mod_role_id())
        mod_perms = new_channel.overwrites_for(mod_role)
        mod_perms.read_messages = True
        mod_perms.manage_messages = True
        await new_channel.set_permissions(mod_role, overwrite=mod_perms)

        # Send user input message and include close button
        message_embed = Embed(description=f"Ticket created by {interaction.user.mention}",
                                      color=get_member_color())
        user_avatar = None
        if interaction.user.avatar != None:
            user_avatar = interaction.user.avatar.url
        message_embed.set_author(name=interaction.user.display_name,
                                 icon_url=user_avatar)
        message_embed.add_field(name="Ticket message:", value=ctx.answer)
        await new_channel.send(embed=message_embed, view=CloseButton(timeout=None))


# Define modal classes for interactive UI on button clicks
class ModModal(ui.Modal):
    answer = ui.TextInput(label="Please let us know how we can assist you.",
                                  style=TextStyle.paragraph,
                                  placeholder="After this initial message, you may submit supporting images.",
                                  required=True, min_length=10)

    async def on_submit(ctx, interaction: Interaction):
        await interaction.response.send_message("Submitting ticket.", ephemeral=True, delete_after=2)
        # Create new ticket and set permissions
        today = datetime.datetime.today()
        ticket_name = f"{today.year}{'%02d' % today.month}{'%02d' % today.day}-{interaction.user.display_name}"
        new_channel = await TicketTool.create_ticket(name=ticket_name.lower(), guild=interaction.guild)
        new_perms = new_channel.overwrites_for(interaction.user)
        new_perms.read_messages = True
        mod_role = utils.get(interaction.guild.roles, name=get_mod_role_id())
        mod_perms = new_channel.overwrites_for(mod_role)
        mod_perms.read_messages = True
        mod_perms.manage_messages = True
        await new_channel.set_permissions(interaction.user, overwrite=new_perms)
        await new_channel.set_permissions(mod_role, overwrite=mod_perms)

        # Send Yupil Bot and user message input embeds; include close button
        mod_embed = Embed(title="Automated Message",
                                  description="A member of the Mod Team will respond when they're available. If you have other information to add to your ticket, such as screenshots or other images, feel free to send them now.\n\nThank you for your patience!",
                                  color=get_yupil_color())
        mod_embed.set_author(name=get_YupilBot_display_name(),
                             icon_url=get_YupilBot_avatar())
        message_embed = Embed(description=f"Ticket created by {interaction.user.mention}",
                                      color=get_member_color())
        user_avatar = None
        if interaction.user.avatar != None:
            user_avatar = interaction.user.avatar.url
        message_embed.set_author(name=interaction.user.display_name,
                                 icon_url=user_avatar)
        message_embed.add_field(name="Initial message:", value=ctx.answer)
        await new_channel.send(f"Welcome, {interaction.user.mention}", embed=mod_embed, view=CloseButton(timeout=None))
        await new_channel.send("\n", embed=message_embed)
