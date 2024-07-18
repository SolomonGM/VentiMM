using System.Net.Http;
using System.Threading.Tasks;
using Moq;
using Moq.Protected;
using Newtonsoft.Json.Linq;
using VentiMM.Sources;
using Xunit;

namespace VentiMM.Tests
{
    public class GetCoinInfoAPITests
    {
        private readonly Mock<HttpMessageHandler> _httpMessageHandlerMock;
        private readonly HttpClient _httpClient;
        private readonly GetCoinInfoAPI _coinInfoAPI;

        public GetCoinInfoAPITests()
        {
            _httpMessageHandlerMock = new Mock<HttpMessageHandler>();
            _httpClient = new HttpClient(_httpMessageHandlerMock.Object) { BaseAddress = new System.Uri("https://api.coingecko.com/api/v3/simple/price") };
            _coinInfoAPI = new GetCoinInfoAPI(_httpClient);
        }

        [Fact]
        public async Task GetCoinPrice_ShouldReturnFormattedPrice()
        {
            // Arrange
            string coin = "bitcoin";
            string responseContent = "{\"bitcoin\":{\"usd\":12345.67}}";

            _httpMessageHandlerMock.Protected()
                .Setup<Task<HttpResponseMessage>>("SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<CancellationToken>())
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = System.Net.HttpStatusCode.OK,
                    Content = new StringContent(responseContent)
                });

            // Act
            var result = await _coinInfoAPI.GetCoinPrice(coin);

            // Assert
            Assert.Equal("12,345.67", result);
        }

        [Fact]
        public async Task GetCoinPrice_ShouldThrowHttpRequestException_OnHttpError()
        {
            // Arrange
            string coin = "bitcoin";

            _httpMessageHandlerMock.Protected()
                .Setup<Task<HttpResponseMessage>>("SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<CancellationToken>())
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = System.Net.HttpStatusCode.BadRequest
                });

            // Act & Assert
            await Assert.ThrowsAsync<HttpRequestException>(() => _coinInfoAPI.GetCoinPrice(coin));
        }

        // ~More Tests here
    }
}
