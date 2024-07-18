using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Discord.WebSocket;
using Discord.Commands;
using Newtonsoft.Json;
using VentiMM.Services;
using VentiMM.Handlers;
using VentiMM.Utilities;
using VentiMM.Extensions;
using Microsoft.Extensions.DependencyInjection;

namespace VentiMM
{
    class Program
    {
        private DiscordSocketClient _client;
        private CommandService _commands;
        private IServiceProvider _services;

        public static async Task Main(string[] args)
        {
            var program = new Program();
            await program.MainAsync();
        }

        public async Task MainAsync()
        {
            var host = CreateHostBuilder().Build();

            _client = host.Services.GetRequiredService<DiscordSocketClient>();
            _commands = host.Services.GetRequiredService<CommandService>();

            var config = host.Services.GetRequiredService<IConfiguration>();

            string token = config["Token"];
            string commandPrefix = config["Prefix"];

            _client.Log += LogAsync;
            _commands.Log += LogAsync;

            _services = ConfigureServices();

            await RegisterCommandsAsync(commandPrefix);

            await _client.LoginAsync(TokenType.Bot, token);
            await _client.StartAsync();

            await host.RunAsync();
        }

        private async Task RegisterCommandsAsync(string commandPrefix)
        {
            _client.MessageReceived += async (message) => await HandleCommandAsync(message, commandPrefix);
            await _commands.AddModulesAsync(Assembly.GetEntryAssembly(), _services);
        }

        private async Task HandleCommandAsync(SocketMessage arg, string commandPrefix)
        {
            var message = arg as SocketUserMessage;
            if (message == null) return;

            var context = new SocketCommandContext(_client, message);

            int argPos = 0;
            if (message.HasStringPrefix(commandPrefix, ref argPos) || message.HasMentionPrefix(_client.CurrentUser, ref argPos))
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

        private IServiceProvider ConfigureServices()
        {
            var services = new ServiceCollection()
                .AddSingleton(_client)
                .AddSingleton(_commands)
                .AddSingleton<StaticSettings>()
                .AddSingleton<GetCoinInfoAPI>()
                .AddSingleton<CommandsModule>()
                .AddLogging(configure => configure.AddConsole())
                .BuildServiceProvider();

            return services;
        }

        public static IHostBuilder CreateHostBuilder() =>
            Host.CreateDefaultBuilder()
                .ConfigureAppConfiguration((context, config) =>
                {
                    config.SetBasePath(Directory.GetCurrentDirectory());
                    config.AddJsonFile("appsettings.json", optional: false, reloadOnChange: true);
                    config.AddEnvironmentVariables();
                })
                .ConfigureLogging(logging =>
                {
                    logging.ClearProviders();
                    logging.AddConsole();
                })
                .ConfigureServices((context, services) =>
                {
                    services.AddSingleton<DiscordSocketClient>();
                    services.AddSingleton<CommandService>();
                    services.AddSingleton<StaticSettings>();
                    services.AddSingleton<GetCoinInfoAPI>();
                    services.AddSingleton<CommandsModule>();
                });
    }
}
