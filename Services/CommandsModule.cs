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
                        var channel = await Context.Guild.CreateTextChannelAsync("Litcoin-1");

                        await channel.AddPermissionOverwriteAsync(Context.Guild.EveryoneRole, OverwritePermissions.DenyAll(channel));
                        await channel.AddPermissionOverwriteAsync(user, new OverwritePermissions(viewChannel: PermValue.Allow, sendMessages: PermValue.Allow));
                        await channel.AddPermissionOverwriteAsync(targetUser, new OverwritePermissions(viewChannel: PermValue.Allow, sendMessages: PermValue.Allow));

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
        public async Task litcoinStatus()
        {
           HttpClient client = new HttpClient();
           try
           {
                var response = await client.GetAsync("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd");
                response.EnsureSuccessStatusCode();

                var responseBody = await response.Content.ReadAsStringAsync();
                var litecoinInfo = JObject.Parse(responseBody)["litecoin"];

                var embed = new EmbedBuilder()
                    .WithThumbnailUrl("https://assets.coingecko.com/coins/images/2/large/litecoin.png?1547033580")
                    .WithTitle("Litecoin (LTC)")
                    .AddField("Price (USD)", $"${litecoinInfo["usd"]} USD")
                    .WithColor(Color.LighterGrey)
                    .Build();

                await ReplyAsync(embed: embed);

           }
           catch (HttpRequestException e)
           {
                Console.WriteLine($"Error getting Litecoin info: {e.Message}");
                await ReplyAsync("Error getting Litecoin info. Please try again later.");
           }
        }

        [Command("bitcoin")]
        public async Task bitcoinStatus()
        {
            HttpClient client = new HttpClient();
            try
            {
                var response = await client.GetAsync("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd");
                response.EnsureSuccessStatusCode();

                var responseBody = await response.Content.ReadAsStringAsync();
                var bitcoinInfo = JObject.Parse(responseBody)["bitcoin"];

                string formattedPrice = string.Format("{0:#,##0.00}", bitcoinInfo["usd"].Value<double>());

                var embed = new EmbedBuilder()
                    .WithThumbnailUrl("https://assets.coingecko.com/coins/images/1/standard/bitcoin.png?1696501400")
                    .WithTitle("Bitcoin (BTC)")
                    .AddField("Price (USD)", $"${formattedPrice} USD")
                    .WithColor(Color.Orange)
                    .Build();

                await ReplyAsync(embed: embed);

            }
            catch (HttpRequestException e)
            {
                Console.WriteLine($"Error getting Bitcoin info: {e.Message}");
                await ReplyAsync("Error getting Bitcoin info. Please try again later.");
                ;
            }
        }
    }
}


