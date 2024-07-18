using System.Threading.Tasks;
using Discord;
using Discord.Commands;
using Discord.WebSocket;
using Microsoft.Extensions.DependencyInjection;
using Moq;
using VentiMM.Services;
using Xunit;

namespace VentiMM.Tests
{
    public class CommandsModuleTests
    {
        private readonly Mock<CommandService> _commandServiceMock;
        private readonly Mock<DiscordSocketClient> _discordSocketClientMock;
        private readonly ServiceProvider _serviceProvider;

        public CommandsModuleTests()
        {
            _commandServiceMock = new Mock<CommandService>();
            _discordSocketClientMock = new Mock<DiscordSocketClient>();

            var services = new ServiceCollection()
                .AddSingleton(_commandServiceMock.Object)
                .AddSingleton(_discordSocketClientMock.Object)
                .AddSingleton<CommandsModule>()
                .AddSingleton(new GetCoinInfoAPI()) // Mock or real API can be injected here
                .BuildServiceProvider();

            _serviceProvider = services;
        }

        [Fact]
        public async Task MemberCount_ShouldReturnCorrectCount()
        {
            // Arrange
            var commandsModule = _serviceProvider.GetRequiredService<CommandsModule>();
            var contextMock = new Mock<SocketCommandContext>();
            var guildMock = new Mock<SocketGuild>();

            guildMock.Setup(g => g.MemberCount).Returns(42);
            contextMock.Setup(c => c.Guild).Returns(guildMock.Object);
            contextMock.Setup(c => c.User).Returns(It.IsAny<SocketUser>());

            commandsModule.SetContext(contextMock.Object);

            // Act
            await commandsModule.MemberCount();

            // Assert
            contextMock.Verify(c => c.Channel.SendMessageAsync("Venti has: 42 members.", false, null, null, null, null, null, null, null, null, null), Times.Once);
        }

        [Fact]
        public async Task Shout_ShouldReplyWithHello()
        {
            // Arrange
            var commandsModule = _serviceProvider.GetRequiredService<CommandsModule>();
            var contextMock = new Mock<SocketCommandContext>();

            commandsModule.SetContext(contextMock.Object);

            // Act
            await commandsModule.Shout();

            // Assert
            contextMock.Verify(c => c.Channel.SendMessageAsync("HELLO!", false, null, null, null, null, null, null, null, null, null, null), Times.Once);
        }

        // ~More Tests here
    }

    public static class CommandModuleExtensions
    {
        public static void SetContext(this ModuleBase<SocketCommandContext> module, SocketCommandContext context)
        {
            var contextField = typeof(ModuleBase<SocketCommandContext>).GetField("_context", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            contextField.SetValue(module, context);
        }
    }
}
