import discord
from discord.ui import View, Button
from discord.ext import tasks, commands
import asyncio

# Configuration specifically for Solana (SOL)
SOL_CHANNEL_CONFIG = {
    "SOL": {
        "embed": discord.Embed(
            title="Solana Support",
            description="You have chosen Solana. Please wait while we connect you with a support representative.",
            color=discord.Color.purple()
        )
    }
}

class TicketView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Deleting ticket...", ephemeral=True)
        await interaction.channel.delete()

async def setup_sol_ticket_channel(bot, channel, user):
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
            "Please mention another user who you will be making a Solana transaction with.\n"
            "For example, you can ping **@john123**.\n\n"
            "Please do not ping staff members or bots."
        ),
        color=discord.Color.green()
    )
    
    await channel.send(embed=prompt_embed)

    def is_user_staff(user):
        return any(role.id in STAFF_ROLES_IDS for role in user.roles)

    def is_user_in_channel(user, channel):
        # Check if user is among members who can see the channel
        return any(member.id == user.id for member in channel.members)

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
        await channel.send(embed=confirmation_embed)
        
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