import discord
from discord.ui import View, Button
from discord.ext import tasks, commands
import asyncio
from dotenv import load_dotenv
from web3 import Web3
import os

load_dotenv()

# Configuration specifically for Ethereum (ETH)
ETH_CHANNEL_CONFIG = {
    "ETH": {
        "embed": discord.Embed(
            title="Ethereum Support",
            description="You have chosen Ethereum. Please wait while we connect you with a support representative.",
            color=discord.Color.blue()
        )
    }
}

class TicketView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user
        self.amount_confirmation_started = False  # Track whether the amount confirmation has started

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.user:
            if not self.amount_confirmation_started:
                # Disable all buttons in this view
                for item in self.children:
                    item.disabled = True
                await interaction.response.edit_message(view=self)

                # Block users from sending messages in the channel
                await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)

                # Send a confirmation message with options to Delete or Continue
                confirmation_embed = discord.Embed(
                    title="Confirm Ticket Deletion",
                    description="Are you sure you want to delete this ticket? All processes will stop, and no one can interact or send messages until you make a decision.",
                    color=discord.Color.red()
                )
                confirmation_view = DeleteConfirmationView(self.user, interaction.channel)
                await interaction.channel.send(embed=confirmation_embed, view=confirmation_view)
            else:
                await interaction.response.send_message(
                    "You cannot cancel the ticket while a transaction is in progress.", ephemeral=True
                )
        else:
            await interaction.response.send_message("Only the ticket creator can cancel the ticket.", ephemeral=True)

    # Helper function to disable cancel button
    async def disable_cancel_button(self, interaction: discord.Interaction):
        """Method to disable the 'Cancel' button when transaction starts."""
        self.children[0].disabled = True  # Disable the 'Cancel' button
        await interaction.message.edit(view=self)  # Update the message with the disabled button

class DeleteConfirmationView(discord.ui.View):
    def __init__(self, user, channel):
        super().__init__(timeout=None)
        self.user = user
        self.channel = channel

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.user:
            await interaction.response.send_message("Deleting the ticket...", ephemeral=True)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("Only the ticket creator can delete the ticket.", ephemeral=True)

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.success)
    async def continue_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.user:
            await interaction.response.send_message("Continuing the process...", ephemeral=True)
            # Re-enable message sending in the channel
            await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
            await interaction.channel.send("The process will now continue, and you can resume your activities.")
        else:
            await interaction.response.send_message("Only the ticket creator can continue the ticket.", ephemeral=True)

class RoleSelectionView(discord.ui.View):
    def __init__(self, bot, user, mentioned_user, ticket_view):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.mentioned_user = mentioned_user
        self.ticket_view = ticket_view

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
        self.ticket_view.amount_confirmation_started = True
        await self.ticket_view.disable_cancel_button(interaction)

        # Remove the role selection embed and buttons
        await interaction.message.delete()

        # Determine roles
        sender = self.user if is_sender else self.mentioned_user
        receiver = self.mentioned_user if is_sender else self.user

        # Send the prompt for the amount to be inputted
        amount_prompt_embed = discord.Embed(
            title="Enter Amount",
            description=f"{sender.mention}, please enter the amount of you will be sending to {receiver.mention}.",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=amount_prompt_embed)

        # Wait for amount input
        try:
            amount_message = await self.bot.wait_for(
                "message",
                timeout=60.0,
                check=lambda m: m.author == sender and m.channel == interaction.channel and m.content.isdigit()
            )

            amount = amount_message.content

            # Confirm the amount with the receiver
            confirm_embed = discord.Embed(
                title="Confirm Amount",
                description=f"{sender.mention} will be sending **${amount}** to {receiver.mention}.\n\n Please confirm if this is correct.",
                color=discord.Color.green()
            )

            confirmation_view = AmountConfirmationView(
                confirm_user=receiver, amount=amount, channel=interaction.channel, bot=self.bot
            )
            await interaction.channel.send(embed=confirm_embed, view=confirmation_view)

        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="Timeout",
                description="You took too long to input an amount. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=timeout_embed)

class AmountConfirmationView(discord.ui.View):
    def __init__(self, confirm_user, amount, channel, bot):
        super().__init__(timeout=None)
        self.confirm_user = confirm_user
        self.amount = float(amount)  # Convert to float for comparison
        self.channel = channel
        self.crypto_address = "0x225753dd8EACe8DaD1d71CB817E8167fF19BE326"  # Load from env variables
        self.bot = bot
        self.w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))  # Initialize web3 with provider

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.confirm_user:
            # Confirm button clicked - start transaction monitoring
            await interaction.message.delete()
            await self.initiate_transaction(interaction.channel)
        else:
            await interaction.response.send_message("Only the receiver can confirm.", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.confirm_user:
            # Cancel button clicked - abort the transaction process
            await interaction.message.delete()

            # Notify the channel that the transaction has been canceled
            canceled_embed = discord.Embed(
                title="Transaction Canceled",
                description="The transaction has been canceled. If you need further assistance, please contact support.",
                color=discord.Color.red()
            )
            canceled_embed.set_footer(text="If you need further assistance, contact support.", 
                                      icon_url="https://cdn-icons-png.flaticon.com/512/564/564619.png")
            await interaction.channel.send(embed=canceled_embed)
        else:
            await interaction.response.send_message("Only the receiver can cancel this transaction.", ephemeral=True)

    # Ethereum transaction logic
    async def initiate_transaction(self, channel):
        confirmation_stage = 0

        address_prompt_embed = discord.Embed(
            title="Send the Cryptocurrency",
            description=(
                f"Please send **${self.amount}** to the following address:\n\n"
                f"`{self.crypto_address}`\n\n"
            ),
            color=discord.Color.blue()
        )
        address_prompt_embed.set_footer(icon_url="https://ima.alfatango.org/images/loader.gif", 
                                        text=f"Awaiting Confirmation status: {confirmation_stage}/3")
        address_prompt_embed.set_thumbnail(url="https://clipground.com/images/ethereum-png-12.png")

        # Create a view for "Paste Address" button
        copy_view = discord.ui.View()
        paste_button = discord.ui.Button(label="Paste Address", style=discord.ButtonStyle.primary)

        async def paste_address_callback(interaction: discord.Interaction):
            await interaction.channel.send(self.crypto_address)
            paste_button.disabled = True
            await interaction.response.edit_message(view=copy_view)

        paste_button.callback = paste_address_callback
        copy_view.add_item(paste_button)

        # Send the embed and buttons
        embed_message = await channel.send(embed=address_prompt_embed, view=copy_view)

        # Start monitoring for the transaction confirmation
        await self.monitor_transaction(channel, embed_message)

    # Monitor Ethereum blockchain for the transaction
    async def monitor_transaction(self, channel, embed_message):
        await channel.send("Monitoring for incoming transactions...")

        try:
            for _ in range(120):  # Monitor for 10 minutes
                latest_block = self.w3.eth.get_block('latest')
                for tx_hash in latest_block['transactions']:
                    transaction = self.w3.eth.get_transaction(tx_hash)
                    if transaction['to'] == self.crypto_address:
                        received_amount = self.w3.from_wei(transaction['value'], 'ether')
                        if received_amount >= self.amount:
                            await self.handle_confirmation_stages(channel, embed_message, transaction, received_amount)
                            return
                await asyncio.sleep(5)  # Wait 5 seconds before checking again

            # If no transaction confirmed after 10 minutes, timeout
            await self.transaction_timeout(channel)

        except ConnectionError as e:
            await self.connection_failed(channel, e)

    # Handle different confirmation stages
    async def handle_confirmation_stages(self, channel, embed_message, transaction, received_amount):
        confirmation_stage = 1
        await self.update_confirmation_embed(embed_message, confirmation_stage)
        await asyncio.sleep(120)  # Wait for 1st confirmation

        confirmation_stage = 2
        await self.update_confirmation_embed(embed_message, confirmation_stage)
        await asyncio.sleep(180)  # Wait for 2nd confirmation

        confirmation_stage = 3
        await self.update_confirmation_embed(embed_message, confirmation_stage)
        await self.confirm_transaction(channel, transaction, received_amount)

    async def update_confirmation_embed(self, embed_message, confirmation_stage):
        address_prompt_embed = discord.Embed(
            title="Send the Cryptocurrency",
            description=f"⏳ Awaiting Confirmation Status: `{confirmation_stage}/3`",
            color=discord.Color.blue()
        )
        await embed_message.edit(embed=address_prompt_embed)

    async def confirm_transaction(self, channel, transaction, received_amount):
        confirmation_embed = discord.Embed(
            title="Transaction Confirmed",
            description=f"Received **{received_amount:.4f} ETH** from `{transaction['from']}`.",
            color=discord.Color.green()
        )
        confirmation_embed.add_field(name="Transaction Hash", value=f"`{transaction['hash'].hex()}`")
        await channel.send(embed=confirmation_embed)

    async def transaction_timeout(self, channel):
        timeout_embed = discord.Embed(
            title="Transaction Timeout",
            description="Transaction not confirmed in time. Please try again or contact support.",
            color=discord.Color.red()
        )
        await channel.send(embed=timeout_embed)

    async def connection_failed(self, channel, error):
        error_embed = discord.Embed(
            title="Connection Error",
            description=f"Error connecting to Ethereum node: {str(error)}",
            color=discord.Color.red()
        )
        await channel.send(embed=error_embed)

# Setup ticket with user interaction
async def setup_eth_ticket_channel(bot, channel, user):
    STAFF_ROLES_IDS = [815867470447116288, 801032011745198080, 799631964835282975, 816052321703952414]

    # Send the initial message in the existing channel
    embed = discord.Embed(
        title=f"Welcome to {channel.mention}",
        description="Our bot will be with you shortly. To close this ticket, press the button below.",
        color=discord.Color.green()
    )
    
    view = TicketView(user=user)
    await channel.send(content=f"{user.mention}", embed=embed, view=view)
    
    # Wait for 10 seconds
    await asyncio.sleep(10)
    
    # Send additional message asking to ping another person
    prompt_embed = discord.Embed(
        title="Add user to transaction ticket",
        description=(
            "Please mention another user who you will be making an Ethereum transaction with.\n"
            "For example, you can ping **@john123**.\n\n"
            "Please do not ping staff members or bots."
        ),
        color=discord.Color.green()
    )
    
    await channel.send(embed=prompt_embed)

    def is_user_staff(user):
        return any(role.id in STAFF_ROLES_IDS for role in user.roles)

    def is_user_in_channel(user, channel):
        return user in channel.members

    def check(message):
        if (
            message.author == user
            and message.channel == channel
            and len(message.mentions) == 1
            and not message.mentions[0].bot
        ):
            mentioned_user = message.mentions[0]
            if not is_user_in_channel(mentioned_user, channel):
                return True
        return False

    try:
        mention_message = await bot.wait_for('message', timeout=60.0, check=check)
        mentioned_user = mention_message.mentions[0]

        if mentioned_user.bot:
            await channel.send("You cannot add a bot to the ticket.")
            return
        if is_user_in_channel(mentioned_user, channel):
            await channel.send("This user is already in the ticket or is a staff member.")
            return
        if is_user_staff(mentioned_user):
            await channel.send("You cannot add a staff member to the ticket. Ping support for help!")
            return
        
        await channel.set_permissions(mentioned_user, read_messages=True, send_messages=True)

        confirmation_embed = discord.Embed(
            title="User Added",
            description=f"{mentioned_user.mention} has been added to the ticket channel {channel.mention}.",
            color=discord.Color.green()
        )
        confirmation_message = await channel.send(embed=confirmation_embed)
        await asyncio.sleep(3)
        await confirmation_message.delete()

        role_selection_embed = discord.Embed(
            title="Where is the crypto going",
            description="Please select your role in this transaction.",
            color=discord.Color.green()
        )
        role_selection_view = RoleSelectionView(bot=bot, user=user, mentioned_user=mentioned_user, ticket_view=view)
        await channel.send(embed=role_selection_embed, view=role_selection_view)

    except asyncio.TimeoutError:
        timeout_embed = discord.Embed(
            title="Timeout",
            description="You took too long to mention another user. Please try again later.",
            color=discord.Color.red()
        )
        await channel.send(embed=timeout_embed)
