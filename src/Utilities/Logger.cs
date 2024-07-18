using Microsoft.Extensions.Logging;

namespace VentiMM.Utilities
{
    public static class Logger
    {
        private static ILogger _logger;

        public static void Initialize(ILogger logger)
        {
            _logger = logger;
        }

        public static void LogInformation(string message)
        {
            _logger?.LogInformation(message);
        }

        public static void LogError(string message)
        {
            _logger?.LogError(message);
        }
    }
}
