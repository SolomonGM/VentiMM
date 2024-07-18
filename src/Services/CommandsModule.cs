using Discord.Commands;
using Discord;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace VentiMM.Services
{
    public class CommandsModule : ModuleBase<SocketCommandContext>
    {
        private readonly GetCoinInfoAPI _coinStats;

        public CommandsModule(GetCoinInfoAPI coinStats)
        {
            _coinStats = coinStats;
        }

        [Command("membercount")]
        [Summary("Displays the current player count.")]
        public async Task MemberCount()
        {
            var guild = Context.Guild;
            var memberCount = guild.MemberCount;

            await ReplyAsync($"Venti has: {memberCount} members.");
        }

        [Command("shout")]
        public async Task Shout()
        {
            await ReplyAsync("HELLO!");
        }

        [Command("create-ticket")]
        public async Task Ticketer()
        {
            var user = Context.User as IGuildUser;

            if (user != null && Context.Guild != null)
            {
                var mentionedUsers = Context.Message.MentionedUsers;

                if (mentionedUsers.Count > 0)
                {
                    var targetUser = mentionedUsers.First() as IGuildUser;

                    if (targetUser != null)
                    {
                        var guild = Context.Guild;

                        var channels = await guild.GetTextChannelsAsync();

                        string ticketName = "Litcoin-";

                        HashSet<int> existingTicketNumbers = new HashSet<int>();
                        foreach (var channel in channels)
                        {
                            if (channel.Name.StartsWith(ticketName) && int.TryParse(channel.Name.Substring(ticketName.Length), out int ticketNumber))
                            {
                                existingTicketNumbers.Add(ticketNumber);
                            }
                        }

                        int newTicketNumber;
                        Random rnd = new Random();
                        do
                        {
                            newTicketNumber = rnd.Next(1000, 10000);
                        } while (existingTicketNumbers.Contains(newTicketNumber));

                        string newChannelName = $"{ticketName}{newTicketNumber}";
                        var newChannel = await guild.CreateTextChannelAsync(newChannelName);

                        var denyAll = new OverwritePermissions(viewChannel: PermValue.Deny, sendMessages: PermValue.Deny);
                        var allowUser = new OverwritePermissions(viewChannel: PermValue.Allow, sendMessages: PermValue.Allow);

                        await newChannel.AddPermissionOverwriteAsync(guild.EveryoneRole, denyAll);
                        await newChannel.AddPermissionOverwriteAsync(user, allowUser);
                        await newChannel.AddPermissionOverwriteAsync(targetUser, allowUser);

                        await ReplyAsync($"Ticket channel created: {newChannel.Mention}. {user.Mention} and {targetUser.Mention} have been added.");
                    }
                    else
                    {
                        await ReplyAsync("Target user was not found!");
                    }
                }
                else
                {
                    await ReplyAsync("You need to mention a user to add to the ticket.");
                }
            }
            else
            {
                await ReplyAsync("Command failed. Please try again.");
            }
        }

        [Command("litcoin")]
        [Alias("LTC")]
        public async Task LitcoinStatus()
        {
            await GetCoinStatus("litecoin", "Litcoin (LTC)", "https://assets.coingecko.com/coins/images/2/standard/litecoin.png?1696501400", Color.Orange);
        }

        [Command("bitcoin")]
        [Alias("BTC")]
        public async Task BitcoinStatus()
        {
            await GetCoinStatus("bitcoin", "Bitcoin (BTC)", "https://assets.coingecko.com/coins/images/1/standard/bitcoin.png?1696501400", Color.Orange);
        }

        [Command("ethereum")]
        [Alias("ETH")]
        public async Task EthereumStatus()
        {
            await GetCoinStatus("ethereum", "Ethereum (ETH)", "https://assets.coingecko.com/coins/images/279/standard/ethereum.png?1696501628", Color.DarkBlue);
        }

        [Command("solana")]
        [Alias("SOL")]
        public async Task SolanaStatus()
        {
            await GetCoinStatus("solana", "Solana (SOL)", "https://assets.coingecko.com/coins/images/4128/standard/solana.png?1696504756", Color.Orange);
        }

        private async Task GetCoinStatus(string coin, string title, string thumbnailUrl, Color color)
        {
            try
            {
                var formattedPrice = await _coinStats.GetCoinPrice(coin);

                var embed = new EmbedBuilder()
                    .WithThumbnailUrl(thumbnailUrl)
                    .WithTitle(title)
                    .AddField("Price (USD)", $"${formattedPrice} USD")
                    .WithColor(color)
                    .Build();

                await ReplyAsync(embed: embed);
            }
            catch (Exception e)
            {
                Console.WriteLine($"Error getting {coin} info: {e.Message}");
                await ReplyAsync($"Error getting {coin} info. Please try again later.");
            }
        }
    }
}
