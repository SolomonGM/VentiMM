using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Discord.WebSocket;
using Discord.Net;
using Newtonsoft.Json;
using Discord;
using Discord.Commands;
using System.Reflection;
using VentiMM.Services;
using Microsoft.Extensions.DependencyInjection;


namespace VentiMM
{
    class Program
    {
        private DiscordSocketClient _client;
        private CommandService _commands;
        private IServiceProvider _services;
        private string _token;
        private string _commandPrefix;

        public static void Main(string[] args)
            => new Program().MainAsync().GetAwaiter().GetResult();

        public async Task MainAsync()
        {
            using (var stream = new FileStream("appsettings.json", FileMode.Open, FileAccess.Read))
            using (var reader = new StreamReader(stream))
            {
                var json = await reader.ReadToEndAsync();
                var config = JsonConvert.DeserializeObject<Config>(json);

                _token = config.Token;
                _commandPrefix = config.Prefix;
            }

            _client = new DiscordSocketClient();
            _commands = new CommandService();

            _client.Log += LogAsync;
            _commands.Log += LogAsync;

            _services = SetupService();

            await RegisterCommandsAsync();

            await _client.LoginAsync(TokenType.Bot, _token);
            await _client.StartAsync();

            await Task.Delay(-1);
        }

        private async Task RegisterCommandsAsync()
        {
            _client.MessageReceived += HandleCommandAsync;
            await _commands.AddModuleAsync<CommandsModule>(_services);
        }

        private async Task HandleCommandAsync(SocketMessage arg)
        {
            var message = arg as SocketUserMessage;
            var context = new SocketCommandContext(_client, message);

            int argPos = 0;
            if(message.HasStringPrefix(_commandPrefix, ref  argPos) || message.HasMentionPrefix(_client.CurrentUser, ref argPos))
            {
                var result = await _commands.ExecuteAsync(context, argPos, _services);
                if (!result.IsSuccess)
                {
                    Console.WriteLine(result.ErrorReason);
                }
            }
        }

        private Task LogAsync(LogMessage log)
        {
            Console.WriteLine(log.ToString());
            return Task.CompletedTask;
        }
        public class Config
        {
            public string Token { get; set; }
            public string Prefix { get; set; }

        }
        private IServiceProvider SetupService()
        {
            var services = new ServiceCollection()
                .AddSingleton(_client)
                .AddSingleton(_commands)
                .BuildServiceProvider();

            return services;
        }
    }
}
