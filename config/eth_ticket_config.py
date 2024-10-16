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

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.user:
            # Disable all buttons in this view
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)

            # Hide all previous embeds by deleting them
            await self.delete_previous_embeds(interaction.channel)

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
            await interaction.response.send_message("Only the ticket creator can cancel the ticket.", ephemeral=True)

    # Helper function to delete previous embeds
    async def delete_previous_embeds(self, channel):
        async for message in channel.history(limit=100):
            if message.embeds:  # Check if the message contains an embed
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass  # Ignore messages that can't be deleted due to permissions


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

            # Optionally, inform users that they can continue using the ticket as before
            await interaction.channel.send("The process will now continue, and you can resume your activities.")
        else:
            await interaction.response.send_message("Only the ticket creator can continue the ticket.", ephemeral=True)

class RoleSelectionView(discord.ui.View):
    def __init__(self, bot, user, mentioned_user):
        super().__init__(timeout=None)
        self.bot = bot
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
            description=f"{sender.mention}, please enter the amount of Ethereum you will be sending to {receiver.mention}.",
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
                description=f"{sender.mention} will be sending **{amount} ETH** to {receiver.mention}.\n\n Please confirm if this is correct.",
                color=discord.Color.green()
            )

            # Pass the bot instance when creating AmountConfirmationView
            confirmation_view = AmountConfirmationView(confirm_user=receiver, amount=amount, channel=interaction.channel, bot=self.bot)

            # Now send the confirm_embed along with the confirmation view
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
        self.crypto_address = os.getenv('BOT_ADDRESS')  # Load from env variables
        self.bot = bot  # Store bot instance for further use
        self.w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))  # Initialize web3 with provider
        self.embed_message = None  # Store the message object to edit later

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.confirm_user:
            await interaction.message.delete()

            confirmation_stage = 0
            
            address_prompt_embed = discord.Embed(
                title="Send the Cryptocurrency",
                description=(
                    f"Please send **{self.amount} ETH** to the following address:\n\n"
                    f"`{self.crypto_address}`\n\n"
                    "Once the bot receives a transaction, you will be notified here.\n\n"
                    f"⏳ Awaiting Confirmation Status: `{confirmation_stage}/3`"
                ),
                color=discord.Color.blue()
            )
            address_prompt_embed.set_thumbnail(url="https://clipground.com/images/ethereum-png-12.png")
            
            # Create a new view for the buttons
            copy_view = discord.ui.View()

            # Define the 'Paste Address' button
            paste_button = discord.ui.Button(label="Paste Address", style=discord.ButtonStyle.primary)

            # Define the callback for the 'Paste Address' button
            async def paste_address_callback(interaction: discord.Interaction):
                await interaction.channel.send(self.crypto_address)

                # Disable button after single use
                paste_button.disabled = True
                
                # Update the message with the disabled button
                await interaction.response.edit_message(view=copy_view)

            # Set the callback for the 'Paste Address' button
            paste_button.callback = paste_address_callback

            # Add the 'Paste Address' button to the view
            copy_view.add_item(paste_button)
            
            # Send the embed with the buttons and store the message object
            self.embed_message = await interaction.channel.send(embed=address_prompt_embed, view=copy_view)

            # Start monitoring for the transaction confirmation
            await self.monitor_transaction(interaction.channel)

        else:
            await interaction.response.send_message("Only the receiver can confirm.", ephemeral=True)

    # Function to monitor Ethereum transactions
    async def monitor_transaction(self, channel):
        await channel.send("Monitoring for incoming transactions...")

        # Start monitoring the blockchain for 10 minutes (600 seconds)
        try:
            for _ in range(120):  # 120 iterations of 5 seconds = 10 minutes
                latest_block = self.w3.eth.get_block('latest')

                for tx_hash in latest_block['transactions']:
                    transaction = self.w3.eth.get_transaction(tx_hash)

                    # Check if the transaction is sent to the correct address
                    if transaction['to'] == self.crypto_address:
                        # Ensure the amount matches the required amount
                        received_amount = self.w3.from_wei(transaction['value'], 'ether')
                        if received_amount >= self.amount:
                            await self.handle_confirmation_stages(channel, transaction, received_amount)
                            return  # Exit the loop once transaction is confirmed

                await asyncio.sleep(5)  # Wait 5 seconds before checking again

            # If no transaction is confirmed after 10 minutes, send a timeout message
            await self.transaction_timeout(channel)
        except ConnectionError as e:
            await self.connection_failed(channel, e)

    # Function to handle confirmation stages
    async def handle_confirmation_stages(self, channel, transaction, received_amount):
        confirmation_stage = 0
        current_block = self.w3.eth.block_number

        # Update to 1st confirmation (wait 2 minutes before next confirmation)
        confirmation_stage = 1
        await self.update_confirmation_embed(confirmation_stage, received_amount)
        await asyncio.sleep(120)  # Wait 2 minutes

        # Update to 2nd confirmation (wait 3 minutes before final confirmation)
        confirmation_stage = 2
        await self.update_confirmation_embed(confirmation_stage, received_amount)
        await asyncio.sleep(180)  # Wait 3 minutes

        # Final confirmation (3/3)
        confirmation_stage = 3
        await self.update_confirmation_embed(confirmation_stage, received_amount)

        # If all 3 confirmations are received, finalize the transaction
        if confirmation_stage == 3:
            await self.confirm_transaction(channel, transaction, received_amount)

    # Function to update confirmation embed
    async def update_confirmation_embed(self, confirmation_stage, received_amount):
        stage_descriptions = ["Pending", "Transaction Received", "Verifing Transaction", "Transaction Confirmed"]

        # Ensure confirmation_stage is within bounds
        if confirmation_stage >= len(stage_descriptions):
            confirmation_stage = len(stage_descriptions) - 1

        # Create the updated embed
        address_prompt_embed = discord.Embed(
            title="Send the Cryptocurrency",
            description=(
                f"Please send **{self.amount} ETH** to the following address:\n\n"
                f"`{self.crypto_address}`\n\n"
                f"⏳ Awaiting Confirmation Status: `{confirmation_stage}/3` - {stage_descriptions[confirmation_stage]}"
            ),
            color=discord.Color.blue()
        )
        address_prompt_embed.set_thumbnail(url="https://clipground.com/images/ethereum-png-12.png")

        # Edit the existing message instead of sending a new one
        if self.embed_message:
            await self.embed_message.edit(embed=address_prompt_embed)

    # Function to confirm the transaction after 3 confirmations
    async def confirm_transaction(self, channel, transaction, received_amount):
        confirmation_embed = discord.Embed(
            title="Transaction Confirmed",
            description=(
                f"A transaction of **{received_amount:.4f} ETH** has been received from `{transaction['from']}`.\n\n"
                "Thank you for completing the transaction."
            ),
            color=discord.Color.green()
        )
        confirmation_embed.add_field(name="Transaction Hash", value=f"`{transaction['hash'].hex()}`")
        confirmation_embed.add_field(name="Amount Received", value=f"{received_amount:.4f} ETH")
        confirmation_embed.add_field(name="Sender", value=f"`{transaction['from']}`")
        
        await channel.send(embed=confirmation_embed)

    # Function to handle transaction timeout
    async def transaction_timeout(self, channel):
        timeout_embed = discord.Embed(
            title="Transaction Timeout",
            description=(
                "The transaction has not been confirmed within the allowed time. "
                "Please ensure you have sent the correct amount to the specified address. "
                "You can try again or contact support."
            ),
            color=discord.Color.red()
        )
        await channel.send(embed=timeout_embed)

    # Function to handle connection errors
    async def connection_failed(self, channel, error):
        error_embed = discord.Embed(
            title="Connection Error",
            description=(
                "There was an issue connecting to the Ethereum node. Please try again later or contact support.\n"
                f"Error Details: `{str(error)}`"
            ),
            color=discord.Color.red()
        )
        await channel.send(embed=error_embed)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.confirm_user:
            await interaction.message.delete()
            canceled_embed = discord.Embed(
                title="Transaction Canceled",
                description="The transaction has been canceled. Please contact support for assistance.",
                color=discord.Color.red()
            )
            canceled_embed.set_footer(text="If you need further assistance, contact support.", icon_url="https://example.com/footer_icon.png")
            await interaction.channel.send(embed=canceled_embed)
        else:
            await interaction.response.send_message("Only the receiver can cancel this transaction.", ephemeral=True)

async def setup_eth_ticket_channel(bot, channel, user):
    # Update to the staff roles of your server
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
    
    # Send the additional message asking to ping another person
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
        role_selection_view = RoleSelectionView(bot=bot, user=user, mentioned_user=mentioned_user)  # Pass bot instance here
        await channel.send(embed=role_selection_embed, view=role_selection_view)
        
    except asyncio.TimeoutError:
        # If the user didn't mention anyone in time, send a timeout message
        timeout_embed = discord.Embed(
            title="Timeout",
            description="You took too long to mention another user. Please try again later.",
            color=discord.Color.red()
        )
        await channel.send(embed=timeout_embed)
