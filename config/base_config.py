import discord
from .btc_config import get_btc_config
from .eth_config import get_eth_config
from .ltc_config import get_ltc_config
from .sol_config import get_sol_config

# Dictionary to hold channel configurations
CHANNEL_CONFIG = {
    "BTC": get_btc_config(),
    "ETH": get_eth_config(),
    "LTC": get_ltc_config(),
    "SOL": get_sol_config(),
    "default": {
        "embed": discord.Embed(
            title="Default Cryptocurrency Channel",
            description="Welcome to the cryptocurrency channel!",
            color=discord.Color.from_rgb(0, 0, 0)
        )
    }
}
