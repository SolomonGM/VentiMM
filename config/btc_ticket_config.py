import discord
from discord.ui import View, Button
from discord.ext import commands
import asyncio

# Configuration specifically for Bitcoin (BTC)
BTC_CHANNEL_CONFIG = {
    "BTC": {
        "embed": discord.Embed(
            title="Bitcoin Support",
            description="You have chosen Bitcoin. Please wait while we connect you with a support representative.",
            color=discord.Color.gold()
        )
    }
}

class TicketView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.user:
            await interaction.response.send_message("Deleting ticket...", ephemeral=True)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("Only the ticket creator can cancel the ticket.", ephemeral=True)

class RoleSelectionView(discord.ui.View):
    def __init__(self, user, mentioned_user):
        super().__init__(timeout=None)
        self.user = user
        self.mentioned_user = mentioned_user

    @discord.ui.button(label="Sender", style=discord.ButtonStyle.green)
    async def sender_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.user:
            await self.finalize_role_selection(interaction, is_sender=True)
        else:
            await interaction.response.send_message("Only the ticket owner can select this option.", ephemeral=True)

    @discord.ui.button(label="Receiver", style=discord.ButtonStyle.danger)
    async def receiver_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.user:
            await self.finalize_role_selection(interaction, is_sender=False)
        else:
            await interaction.response.send_message("Only the ticket owner can select this option.", ephemeral=True)

    async def finalize_role_selection(self, interaction: discord.Interaction, is_sender: bool):
        # Remove the role selection embed and buttons
        await interaction.message.delete()

        # Determine roles
        sender = self.user if is_sender else self.mentioned_user
        receiver = self.mentioned_user if is_sender else self.user

        # Send the prompt for the amount to be inputted
        amount_prompt_embed = discord.Embed(
            title="Enter Amount",
            description=f"{sender.mention}, please enter the amount of Bitcoin you will be sending to {receiver.mention}.",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=amount_prompt_embed)

        # Wait for amount input
        try:
            amount_message = await bot.wait_for(
                "message",
                timeout=60.0,
                check=lambda m: m.author == sender and m.channel == interaction.channel and m.content.isdigit()
            )

            amount = amount_message.content

            # Confirm the amount with the receiver
            confirm_embed = discord.Embed(
                title="Confirm Amount",
                description=f"{sender.mention} will be sending **{amount} BTC** to {receiver.mention}. Please confirm if this is correct.",
                color=discord.Color.green()
            )

            confirmation_view = AmountConfirmationView(confirm_user=receiver, amount=amount)
            await interaction.channel.send(embed=confirm_embed, view=confirmation_view)

        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="Timeout",
                description="You took too long to input an amount. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=timeout_embed)

class AmountConfirmationView(discord.ui.View):
    def __init__(self, confirm_user, amount):
        super().__init__(timeout=None)
        self.confirm_user = confirm_user
        self.amount = amount

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only allow the designated confirm user to confirm the amount
        if interaction.user == self.confirm_user:
            await interaction.message.delete()
            confirmed_embed = discord.Embed(
                title="Transaction Confirmed",
                description=f"{self.confirm_user.mention} has confirmed the amount of **{self.amount} BTC**. The transaction will proceed.",
                color=discord.Color.green()
            )
            await interaction.channel.send(embed=confirmed_embed)
        else:
            await interaction.response.send_message("Only the designated user can confirm this transaction.", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only allow the designated confirm user to cancel the transaction
        if interaction.user == self.confirm_user:
            await interaction.message.delete()
            canceled_embed = discord.Embed(
                title="Transaction Canceled",
                description="The transaction has been canceled. Please contact support for assistance.",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=canceled_embed)
        else:
            await interaction.response.send_message("Only the designated user can cancel this transaction.", ephemeral=True)

async def setup_btc_ticket_channel(bot, channel, user):
    # Update to the staff roles of your server
    STAFF_ROLES_IDS = [815867470447116288, 801032011745198080, 799631964835282975, 816052321703952414]

    # Send the initial message in the existing channel
    embed = discord.Embed(
        title=f"Welcome to {channel.mention}",
        description="Our bot will be with you shortly. To close this ticket, press the button below.",
        color=discord.Color.green()
    )
    
    view = TicketView(user=user)
    await channel.send(content=f"{user.mention} Welcome", embed=embed, view=view)
    
    # Wait for 10 seconds
    await asyncio.sleep(10)
    
    # Send the additional message asking to ping another person
    prompt_embed = discord.Embed(
        title="Add user to transaction ticket",
        description=(
            "Please mention another user who you will be making a Bitcoin transaction with.\n"
            "For example, you can ping **@john123**.\n\n"
            "Please do not ping staff members or bots."
        ),
        color=discord.Color.green()
    )
    
    await channel.send(embed=prompt_embed)

    def is_user_staff(user):
        return any(role.id in STAFF_ROLES_IDS for role in user.roles)

    def is_user_in_channel(user, channel):
        # Check if user is already in the channel
        return user in channel.members

    def check(message):
        # Check if the message is from the same user and in the same channel
        # Check if the message mentions exactly one user
        if (
            message.author == user
            and message.channel == channel
            and len(message.mentions) == 1
            and not message.mentions[0].bot
        ):
            mentioned_user = message.mentions[0]
            # Check if the mentioned user is not already in the channel
            if not is_user_in_channel(mentioned_user, channel):
                return True
        return False

    try:
        # Use the bot instance to wait for the message
        mention_message = await bot.wait_for('message', timeout=60.0, check=check)
        
        # Get the mentioned user
        mentioned_user = mention_message.mentions[0]

        # Check if the mentioned user is a bot or staff
        if mentioned_user.bot:
            await channel.send("You cannot add a bot to the ticket.")
            return

        # Check if the mentioned user is already in the channel
        if is_user_in_channel(mentioned_user, channel):
            await channel.send("This user is already in the ticket or is a staff member.")
            return
        
        # Check if the mentioned user is a staff member
        if is_user_staff(mentioned_user):
            await channel.send("You cannot add a staff member to the ticket. Ping support for help!")
            return
        
        # Add the mentioned user to the channel
        await channel.set_permissions(mentioned_user, read_messages=True, send_messages=True)
        
        # Send confirmation message
        confirmation_embed = discord.Embed(
            title="User Added",
            description=f"{mentioned_user.mention} has been added to the ticket channel {channel.mention}.",
            color=discord.Color.green()
        )
        confirmation_message = await channel.send(embed=confirmation_embed)

        # Delete the "User Added" embed after 3 seconds to reduce clutter
        await asyncio.sleep(3)
        await confirmation_message.delete()

        # Send the transaction role selection embed
        role_selection_embed = discord.Embed(
            title="Where is the crypto going",
            description="Please select your role in this transaction.",
            color=discord.Color.green()
        )
        role_selection_view = RoleSelectionView(user=user, mentioned_user=mentioned_user)
        await channel.send(embed=role_selection_embed, view=role_selection_view)
        
    except asyncio.TimeoutError:
        # If the user didn't mention anyone in time, send a timeout message
        timeout_embed = discord.Embed(
            title="Timeout",
            description="You took too long to mention another user. Please try again later.",
            color=discord.Color.red()
        )
        await channel.send(embed=timeout_embed)
    except Exception as e:
        print(f"An error occurred: {e}")
