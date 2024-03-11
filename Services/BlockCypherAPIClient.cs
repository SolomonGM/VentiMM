using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Net.Http;
using RestSharp;

//Implement coinGecko APi
namespace Test_VentiMM.Sources
{
    class BlockCypherAPIClient
    {
        private string apiBaseUrl = "";
        public string GetLitcoinWallet()
        {
            string Api_URL = "https://api.blockcypher.com/v1/example_endpoint?token=" + apiToken;

            HttpClient client = new HttpClient();
            HttpResponseMessage response = client.GetAsync(Api_URL).Result;

            if (response.IsSuccessStatusCode)
            {
                string responseContent = response.Content.ReadAsStringAsync().Result;
                return responseContent;
            }
            else
            {
                Console.WriteLine("Error: " + response.StatusCode);
                return null;
            }
        }

    }
}

