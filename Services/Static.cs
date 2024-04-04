using Discord;
using Discord.Commands;
using Discord.WebSocket;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;

namespace Test_VentiMM.Sources
{
    class StaticSettings : ModuleBase<SocketCommandContext>
    {
        private static DiscordSocketClient _client;
        public static void SetClient(DiscordSocketClient client)
        {
            _client = client;
        }

        public static async Task CryptoDropdownPrompt(ulong channelId, string messageText, List<string> options)
        {
            if(_client == null)
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

            var embed = new EmbedBuilder()
                .WithTitle("Cryptocurrency MiddleMan")
                .WithImageUrl("C:\\Users\\sadjm\\source\\repos\\Test-VentiMM\\Assets\\VentiMM-logo.png")
                .WithDescription(messageText)
                .WithColor(Color.Blue)
                .Build();

            var message = await channel.SendMessageAsync(embed: embed);

           var selectionMenuOptions = new List<SelectMenuOptionBuilder>();
           foreach(var option in options)
            {
                selectionMenuOptions.Add(new SelectMenuOptionBuilder()
                    .WithLabel(option)
                    .WithValue(option)
                    .WithDescription($"Select {option}"));  
            }

            // Create the dropdown menu
            var dropdown = new ComponentBuilder()
                .WithSelectMenu("Select a crypto coin", selectionMenuOptions, placeholder: "Select a coin")
                .Build();

            // Send the message with the dropdown menu
            await message.ModifyAsync(msg => msg.Components = new Optional<MessageComponent>(dropdown));
        }
    }
}
