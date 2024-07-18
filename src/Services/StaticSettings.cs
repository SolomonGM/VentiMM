using Discord;
using Discord.Commands;
using Discord.WebSocket;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Test_VentiMM.Sources
{
    public class StaticSettings : ModuleBase<SocketCommandContext>
    {
        private static DiscordSocketClient _client;

        public static void SetClient(DiscordSocketClient client)
        {
            _client = client;
        }

        [Command("initclient")]
        [Summary("Initializes the bot client.")]
        public async Task InitClient()
        {
            SetClient(Context.Client as DiscordSocketClient);
            await ReplyAsync("Client initialized.");
        }

        public static async Task CryptoDropdownPrompt(ulong channelId, string messageText, List<string> options)
        {
            if (_client == null)
            {
                Console.WriteLine("Client not initialized.");
                return;
            }

            var channel = _client.GetChannel(channelId) as IMessageChannel;

            if (channel == null)
            {
                Console.WriteLine($"Channel with ID {channelId} not found.");
                return;
            }

            try
            {
                var embed = new EmbedBuilder()
                    .WithTitle("Cryptocurrency MiddleMan")
                    .WithThumbnailUrl("https://example.com/path-to-your-logo.png")
                    .WithDescription(messageText)
                    .WithColor(Color.Blue)
                    .AddField("Instructions", "Select a cryptocurrency from the dropdown menu below.")
                    .WithFooter(footer => footer.Text = $"Requested by {_client.CurrentUser.Username}")
                    .Build();

                var message = await channel.SendMessageAsync(embed: embed);

                var selectionMenuOptions = new List<SelectMenuOptionBuilder>();
                foreach (var option in options)
                {
                    selectionMenuOptions.Add(new SelectMenuOptionBuilder()
                        .WithLabel(option)
                        .WithValue(option)
                        .WithDescription($"Select {option}"));
                }

                // Create the dropdown menu
                var dropdown = new ComponentBuilder()
                    .WithSelectMenu("crypto_select_menu", selectionMenuOptions, placeholder: "Select a coin")
                    .Build();

                // Send the message with the dropdown menu
                await message.ModifyAsync(msg => msg.Components = new Optional<MessageComponent>(dropdown));
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error sending crypto dropdown prompt: {ex.Message}");
            }
        }

        [Command("cryptodropdown")]
        [Summary("Sends a cryptocurrency selection prompt.")]
        public async Task SendCryptoDropdown()
        {
            var options = new List<string> { "Bitcoin", "Ethereum", "Litecoin", "Solana" };
            await CryptoDropdownPrompt(Context.Channel.Id, "Please select a cryptocurrency:", options);
        }
    }
}
