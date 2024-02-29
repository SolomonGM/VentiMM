using Discord.Commands;
using Discord;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

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
    }
}

