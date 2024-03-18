using Discord;
using Discord.Commands;
using Discord.WebSocket;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using VentiMM;

namespace Test_VentiMM.Sources
{
    class StaticSettings
    {
        /* public static async Task CryptoDropdownPrompt(ulong channelId, string messageText, List<string> options)
        {
            var channel = _client.GetChannel(channelId) as IMessageChannel;
            if (channel == null)
            {
                Console.WriteLine($"Channel with ID {channelId} not found.");
                return;
            }

            var embed = new EmbedBuilder()
                .WithTitle("Dropdown Prompt")
                .WithDescription(messageText)
                .WithColor(Color.Blue)
                .Build();

            var message = await channel.SendMessageAsync(embed: embed);

            // Create the dropdown menu
            var dropdown = new ComponentBuilder()
                .WithSelectMenu("dropdown-menu", "Choose an option", options)
                .Build();

            // Send the message with the dropdown menu
            await message.ModifyAsync(msg => msg.Components = new Optional<ActionRowComponent[]> { dropdown });
        } */
    }
}
