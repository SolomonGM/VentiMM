using System;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;
using Polly;
using Polly.Retry;

namespace VentiMM.Sources
{
    public class GetCoinInfoAPI
    {
        private readonly HttpClient _client;
        private readonly string _baseApiUrl;
        private readonly RetryPolicy<HttpResponseMessage> _retryPolicy;

        public GetCoinInfoAPI(string baseApiUrl = "https://api.coingecko.com/api/v3/simple/price")
        {
            _client = new HttpClient();
            _baseApiUrl = baseApiUrl;

            // Define a retry policy: Retry 3 times with an exponential backoff
            _retryPolicy = Policy
                .HandleResult<HttpResponseMessage>(r => !r.IsSuccessStatusCode)
                .WaitAndRetryAsync(3, retryAttempt => TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)),
                    onRetry: (response, delay, retryCount, context) =>
                    {
                        Console.WriteLine($"Request failed. Waiting {delay} before next retry. Retry attempt {retryCount}");
                    });
        }

        public async Task<string> GetCoinPrice(string coin)
        {
            try
            {
                string apiURL = $"{_baseApiUrl}?ids={coin}&vs_currencies=usd";

                var response = await _retryPolicy.ExecuteAsync(() => _client.GetAsync(apiURL));
                response.EnsureSuccessStatusCode();

                string responseBody = await response.Content.ReadAsStringAsync();
                JObject coinInfo = JObject.Parse(responseBody);

                double coinUsd = coinInfo[co
