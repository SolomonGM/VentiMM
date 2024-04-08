using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Net.Http;
using Newtonsoft.Json.Linq;

namespace Test_VentiMM.Sources
{
    class GetCoinInfoAPI
    {
        private readonly HttpClient client = new HttpClient();

        public async Task<string> GetCoinPrice(string coin)
        {
            try
            {
                string apiURL = "https://api.coingecko.com/api/v3/simple/price?ids=" + coin + "&vs_currencies=usd";
                var response = await client.GetAsync(apiURL);
                response.EnsureSuccessStatusCode();

                string responseBody = await response.Content.ReadAsStringAsync();
                JObject CoinInfo = JObject.Parse(responseBody);


                double CoinUsd = CoinInfo[coin]["usd"].Value<double>();

                string formattedPrice = string.Format("{0:#,##0.00}", CoinUsd);

                return formattedPrice;
            }
            catch (HttpRequestException e)
            {
                Console.WriteLine($"HTTP ERROR: {e.Message}");
                throw;
            }
            catch (Exception e)
            {
                Console.WriteLine($"ERROR: {e.Message}");
                throw;
            }
        }
    }
}
