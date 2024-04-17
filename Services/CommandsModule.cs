using Discord.Commands;
using Discord;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Test_VentiMM.Sources;
using Newtonsoft.Json.Linq;
using System.Net.Http;

namespace VentiMM.Services
{
    public class CommandsModule : ModuleBase<SocketCommandContext>
    {
        private readonly GetCoinInfoAPI _coinStats;

        public CommandsModule()
        {
            _coinStats = new GetCoinInfoAPI();
        }

        [Command("membercount")]
        [Summary("Displays the current player count.")]
        public async Task MemeberCount()
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
                var mentionedUser = Context.Message.MentionedUsers;

                if (mentionedUser.Count > 0)
                {
                    var targetUser = mentionedUser.First() as IGuildUser;

                    if (targetUser != null)
                    {
                        var guild = Context.Guild;

                        var channel = await guild.GetTextChannelsAsync();

                        string ticketName = "Litcoin-";

                        HashSet<int> existingTicketNumbers = new HashSet<int>();
                        foreach(var channels in channel)
                        {
                            if (channel.Name.StartsWith(ticketName) && int.TryParse(channel.Name.Substrings(ticketName.Length), out int ticketNumber))
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
                        await guild.CreateTextChannelAsync(newChannelName);

                        await channels.AddPermissionOverwriteAsync(Context.Guild.EveryoneRole, OverwritePermissions.DenyAll(channels));
                        await channels.AddPermissionOverwriteAsync(user, new OverwritePermissions(viewChannel: PermValue.Allow, sendMessages: PermValue.Allow));
                        await channels.AddPermissionOverwriteAsync(targetUser, new OverwritePermissions(viewChannel: PermValue.Allow, sendMessages: PermValue.Allow));

                        await ReplyAsync($"Ticket channel created. {user.Mention} and {targetUser.Mention} have been added.");
                    }
                    else
                    {
                        await ReplyAsync("Target user was not found!");
                    }
                }
                else
                {
                    await ReplyAsync("You did not enter the command properly, please try again!");
                }   
            }
        }

        [Command("litcoin")]
        [Alias("LTC")]
        public async Task LitcoinStatus()
        {
            try
            {
                string coin = "litcoin";
                var formattedPrice = await _coinStats.GetCoinPrice(coin);


                var embed = new EmbedBuilder()
                    .WithThumbnailUrl("https://assets.coingecko.com/coins/images/2/standard/litecoin.png?1696501400")
                    .WithTitle("Litcoin (LTC)")
                    .AddField("Price (USD)", $"${formattedPrice} USD")
                    .WithColor(Color.Orange)
                    .Build();

                await ReplyAsync(embed: embed);
            }
            catch (Exception e)
            {
                Console.WriteLine($"Error getting Litcoin info: {e.Message}");
                await ReplyAsync("Error getting Litcoin info. Please try again later.");
            }
        }

        [Command("bitcoin")]
        [Alias("BTC")]
        public async Task BitcoinStatus()
        {
            try
            {
                string coin = "bitcoin";
                var formattedPrice = await _coinStats.GetCoinPrice(coin);


                var embed = new EmbedBuilder()
                    .WithThumbnailUrl("https://assets.coingecko.com/coins/images/1/standard/bitcoin.png?1696501400")
                    .WithTitle("Bitcoin (BTC)")
                    .AddField("Price (USD)", $"${formattedPrice} USD")
                    .WithColor(Color.Orange)
                    .Build();

                await ReplyAsync(embed: embed);
            }
            catch (Exception e)
            {
                Console.WriteLine($"Error getting Bitcoin info: {e.Message}");
                await ReplyAsync("Error getting Bitcoin info. Please try again later.");
            }
        }

        [Command("ethereum")]
        [Alias("eth")]
        public async Task EthereumStatus()
        {
            try
            {
                string coin = "ethereum";
                var formattedPrice = await _coinStats.GetCoinPrice(coin);


                var embed = new EmbedBuilder()
                    .WithThumbnailUrl("https://assets.coingecko.com/coins/images/279/standard/ethereum.png?1696501628")
                    .WithTitle("Ethereum (ETH)")
                    .AddField("Price (USD)", $"${formattedPrice} USD")
                    .WithColor(Color.DarkBlue)
                    .Build();

                await ReplyAsync(embed: embed);
            }
            catch (Exception e)
            {
                Console.WriteLine($"Error getting Ethereum info: {e.Message}");
                await ReplyAsync("Error getting Ethereum info. Please try again later.");
            }
        }

        [Command("Solana")]
        [Alias("SOL")]
        public async Task SolanaStatus()
        {
            try
            {
                string coin = "Solana";
                var formattedPrice = await _coinStats.GetCoinPrice(coin);

                var embed = new EmbedBuilder()
                    .WithThumbnailUrl("https://assets.coingecko.com/coins/images/4128/standard/solana.png?1696504756")
                    .WithTitle("Solana (SOL)")
                    .AddField("Price (USD)", $"${formattedPrice} USD")
                    .WithColor(Color.Orange)
                    .Build();

                await ReplyAsync(embed: embed);
            }
            catch (Exception e)
            {
                Console.WriteLine($"Error getting Solana info: {e.Message}");
                await ReplyAsync("Error getting Solana info. Please try again later.");
            }
        }
    }
}
