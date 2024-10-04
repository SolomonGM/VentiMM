from web3 import Web3
from web3 import EthereumTesterProvider

#def incoming_transactions():


#def outgoing_transactions():


provider_url = 'https://mainnet.infura.io/v3/16333b90a3b74381a14aa7a31424824b'; 

w3 = Web3.HTTPProvider(provider_url)

w3.is_connected()

address = '0x7FD6D45F7780b84a63E8CE18db699045a5fcb2f9';
Web3.is_address(address)

wallet = Web3.to_checksum_address(address)

Web3.eth.get_balance(wallet)

Web3.from_wei(11111111111111111111111, 'ether')
