# <img width="30px" src="Screenshot 2024-02-27 223018.png"> VentiMM

VentiMM, developed using Discord.NET, offers a middleman service for facilitating cryptocurrency trades within Discord servers. The bot acts as a trusted intermediary between two parties engaging in a cryptocurrency transaction, ensuring security and trust throughout the trade process.

## Features

- **Middleman Service**: The bot provides a secure platform for users to conduct cryptocurrency trades with confidence, minimizing the risk of scams or fraudulent activities.
- **Automated Escrow**: Utilizing smart contract principles, the bot securely holds the cryptocurrency being traded until both parties confirm the completion of the transaction.
- **Transaction Monitoring**: The bot tracks the progress of trades and notifies users at each stage, ensuring transparency and accountability.
- **Cryptocurrency Information**: Users can request real-time information about the current status of various cryptocurrencies, including price, market cap, volume, and more.
- **Secure Transactions**: With Discord.NET's robust security features, transactions are conducted securely to safeguard users' assets.

## Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:

- You have a Discord account.
- You have administrative access to the Discord server where you want to add the bot.
- You have .NET Core SDK installed on your development machine.

### Installation

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/yourusername/VentiMM.git
   cd VentiMM
   
2. **Install dependencies**:
   ```sh
   dotnet restore

3. **Confidure the bot**:
   - Create a file named `appsettings.json` in the root directory of the project.
   - Add your Discord bot token and other configuration settings to `appsettings.json`:
   ```sh
   {
     "DiscordToken": "YOUR_DISCORD_BOT_TOKEN",
     "DatabaseConnectionString": "YOUR_DATABASE_CONNECTION_STRING"
   }

2. **Run the bot**:
   ```sh
   dotnet run
   
   
