using Discord.Commands;

namespace VentiMM.Extensions
{
    public static class CommandContextExtensions
    {
        public static void SetContext(this ModuleBase<SocketCommandContext> module, SocketCommandContext context)
        {
            var contextField = typeof(ModuleBase<SocketCommandContext>).GetField("_context", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            contextField.SetValue(module, context);
        }
    }
}
