import asyncio
import json
import os
import random
import string
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks
from web3 import Web3

# Load configuration from config.json
with open('config/config.json', 'r') as config_file:
    config = json.load(config_file)

DISCORD_TOKEN = config.get('DISCORD_TOKEN')
CHANNEL_ID = int(config.get('CHANNEL_ID'))

if DISCORD_TOKEN is None:
    raise ValueError("No bot token found in configuration file.")
if CHANNEL_ID is None:
    raise ValueError("No channel ID found in configuration file.")

MAX_CHANNELS_PER_USER = 8
TIME_WINDOW = timedelta(minutes=10)
BUTTON_RESET_INTERVAL = timedelta(minutes=10)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="v!", intents=intents)

from config.btc_ticket_config import setup_btc_ticket_channel, BTC_CHANNEL_CONFIG
from config.eth_ticket_config import setup_eth_ticket_channel, ETH_CHANNEL_CONFIG
from config.sol_ticket_config import setup_sol_ticket_channel, SOL_CHANNEL_CONFIG
from config.ltc_ticket_config import setup_ltc_ticket_channel, LTC_CHANNEL_CONFIG

CHANNEL_CONFIG = {**BTC_CHANNEL_CONFIG, **ETH_CHANNEL_CONFIG, **SOL_CHANNEL_CONFIG, **LTC_CHANNEL_CONFIG}

def load_user_channel_data():
    if not os.path.exists('user_channel_data.json'):
        return {}
    with open('user_channel_data.json', 'r') as f:
        data = json.load(f)
        for user_id, timestamps in data.items():
            data[user_id] = [datetime.fromisoformat(ts) for ts in timestamps]
        return data

def save_user_channel_data(user_channel_data):
    with open('user_channel_data.json', 'w') as f:
        data = {user_id: [ts.isoformat() for ts in timestamps] for user_id, timestamps in user_channel_data.items()}
        json.dump(data, f)

def load_created_channels():
    if not os.path.exists('created_channels.json'):
        return []
    with open('created_channels.json', 'r') as f:
        return json.load(f)

def save_created_channels(channels):
    with open('created_channels.json', 'w') as f:
        json.dump(channels, f)

class CryptoSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Choose a cryptocurrency...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Ethereum", value="ETH", description="ETH", emoji=":ethereum:1274259375732691107"),
                discord.SelectOption(label="Bitcoin", value="BTC", description="BTC", emoji=":bitcoin:1274259378056331317"),
                discord.SelectOption(label="Solana", value="SOL", description="SOL", emoji=":solana:1274259316517638256"),
                discord.SelectOption(label="Litecoin", value="LTC", description="LTC", emoji=":litcoin:1274259398528860200")
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        chosen_crypto = self.values[0].upper()

        user_channel_data = load_user_channel_data()
        user_id = str(interaction.user.id)

        now = datetime.utcnow()
        if user_id in user_channel_data:
            timestamps = [ts for ts in user_channel_data[user_id] if now - ts < TIME_WINDOW]

            if len(timestamps) >= MAX_CHANNELS_PER_USER:
                await interaction.followup.send("You have reached your channel creation limit.", ephemeral=True)
                return

            timestamps.append(now)
            user_channel_data[user_id] = timestamps
        else:
            user_channel_data[user_id] = [now]

        save_user_channel_data(user_channel_data)

        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
        channel_name = f"{chosen_crypto}-{random_id}"

        guild = interaction.guild
        member = interaction.user
        config_data = CHANNEL_CONFIG.get(chosen_crypto)

        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True),
            }

            channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
            created_channels = load_created_channels()
            created_channels.append(channel.id)
            save_created_channels(created_channels)

            embed = config_data.get("embed")
            if embed:
                await channel.send(embed=embed)

            setup_function = {
                "BTC": setup_btc_ticket_channel,
                "ETH": setup_eth_ticket_channel,
                "SOL": setup_sol_ticket_channel,
                "LTC": setup_ltc_ticket_channel
            }.get(chosen_crypto)

            if setup_function:
                await setup_function(interaction.client, channel, member)

            await interaction.followup.send(f"Channel created: {channel_name}!", ephemeral=True)

        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send(f"Failed to create channel: {e}", ephemeral=True)

class CryptoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.add_item(CryptoSelect())
        self.middleman_button = None

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

    async def reset_middleman_button(self):
        if self.middleman_button:
            self.middleman_button.disabled = False
            if self.message:
                try:
                    await self.message.edit(view=self)
                except discord.NotFound:
                    pass

class MiddlemanButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Middleman", style=discord.ButtonStyle.primary, custom_id="middleman_button")

    async def callback(self, interaction: discord.Interaction):
        view = CryptoView()
        await interaction.response.edit_message(content="", view=view)
        view.message = interaction.message
        view.middleman_button = self

        bot.loop.create_task(reset_button_task(view))

async def setup_channel(bot):
    guild = discord.utils.get(bot.guilds)

    if guild:
        channel = guild.get_channel(CHANNEL_ID)
        if channel is None:
            channel = await guild.create_text_channel(name="cryptocurrency")

        embed = discord.Embed(
            title="Cryptocurrency",
            description=(
                "__Fees__\n"
                "**Deals $500+: 5%**\n"
                "**Deals under $500: 3%**\n"
                "**Deals under $50: FREE**\n"
                "\nClick the button below to select a cryptocurrency."
            ),
            color=discord.Color.from_rgb(0, 0, 0)
        )
        
        view = discord.ui.View()
        middleman_button = MiddlemanButton()
        view.add_item(middleman_button)

        messages = [message async for message in channel.history(limit=1)]
        if messages:
            last_message = messages[0]
            if last_message.author.id == bot.user.id:
                await last_message.edit(embed=embed, view=view)
            else:
                await channel.send(embed=embed, view=view)
        else:
            await channel.send(embed=embed, view=view)

@tasks.loop(minutes=2)
async def reset_button_task(view):
    await view.reset_middleman_button()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await setup_channel(bot)
    
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            await bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(DISCORD_TOKEN)
