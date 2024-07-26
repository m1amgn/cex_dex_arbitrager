import os
from dotenv import load_dotenv

load_dotenv()


class Network:
    def __init__(self,
                 name: str,
                 rpc: str,
                 chain_id: int,
                 eip1559_tx: bool,
                 coin_symbol: str,
                 explorer: str,
                 explorer_api_abi: str,
                 api_key: str,
                 ):
        self.name = name
        self.rpc = rpc
        self.chain_id = chain_id
        self.eip1559_tx = eip1559_tx
        self.coin_symbol = coin_symbol
        self.explorer = explorer
        self.explorer_api_abi = explorer_api_abi
        self.api_key = api_key

    def __str__(self):
        return f"{self.name}"


Ethereum = Network(
    name="Ethereum",
    rpc="https://eth.drpc.org",
    chain_id=1,
    eip1559_tx=True,
    coin_symbol="ETH",
    explorer="https://etherscan.io/",
    explorer_api_abi="https://api.etherscan.io/api?module=contract&action=getabi&address=",
    api_key=os.getenv("ETHERSCAN_API_KEY")
)


Arbitrum = Network(
    name="Arbitrum",
    rpc="https://arbitrum-one.public.blastapi.io",
    chain_id=42161,
    eip1559_tx=True,
    coin_symbol="ETH",
    explorer="https://arbiscan.io/",
    explorer_api_abi="https://api.arbiscan.io/api?module=contract&action=getabi&address=",
    api_key=os.getenv("ARBISCAN_API_KEY")
)


Optimism = Network(
    name="Optimism",
    rpc="https://rpc.ankr.com/optimism/",
    chain_id=10,
    eip1559_tx=True,
    coin_symbol="ETH",
    explorer="https://optimistic.etherscan.io/",
    explorer_api_abi="https://api-optimistic.etherscan.io/api?module=contract&action=getabi&address=",
    api_key=os.getenv("OPTIMISTICSCAN_API_KEY")
)


Polygon = Network(
    name="Polygon",
    rpc="https://polygon-rpc.com/",
    chain_id=137,
    eip1559_tx=True,
    coin_symbol="MATIC",
    explorer="https://polygonscan.com/",
    explorer_api_abi="https://api.polygonscan.com/api?module=contract&action=getabi&address=",
    api_key=os.getenv("POLYGONSCAN_API_KEY")
)


Avalanche = Network(
    name="Avalanche C-Chain",
    rpc="https://rpc.ankr.com/avalanche/",
    chain_id=43114,
    eip1559_tx=True,
    coin_symbol="AVAX",
    explorer="https://snowtrace.io/",
    explorer_api_abi="https://api.snowtrace.io/api?module=contract&action=getabi&address=",
    api_key=os.getenv("SNOWTRACE_API_KEY")
)


BinanceSmartChain = Network(
    name='BNB Smart Chain (BEP20)',
    rpc='https://bsc-dataseed.binance.org/',
    chain_id=56,
    eip1559_tx=False,
    coin_symbol='BNB',
    explorer='https://bscscan.com/',
    explorer_api_abi='https://api.bscscan.com/api?module=contract&action=getabi&address=',
    api_key=os.getenv("BSCSCAN_API_KEY")
)


Base = Network(
    name='Base',
    rpc='https://base.api.onfinality.io/public',
    chain_id=8453,
    eip1559_tx=True,
    coin_symbol='ETH',
    explorer='https://basescan.org/',
    explorer_api_abi='https://api.basescan.org/api?module=contract&action=getabi&address=',
    api_key=os.getenv("BASESCAN_API_KEY")
)


Solana = Network(
    name='Solana',
    rpc='https://api.mainnet-beta.solana.com',
    chain_id=101,
    eip1559_tx=False,
    coin_symbol='SOL',
    explorer='https://solscan.io/',
    explorer_api_abi='',
    api_key=''
)


Fantom = Network(
    name='fantom',
    rpc='https://rpc.ankr.com/fantom/',
    chain_id=250,
    eip1559_tx=True,
    coin_symbol='FTM',
    explorer='https://ftmscan.com/',
    explorer_api_abi="",
    api_key=""
)


ZkSync = Network(
    name='zkSync Era',
    rpc='https://mainnet.era.zksync.io/',
    chain_id=324,
    eip1559_tx=False,
    coin_symbol='ETH',
    explorer='https://explorer.zksync.io/',
    explorer_api_abi='',
    api_key=''
)


Osmosis = Network(
    name='Osmosis',
    rpc='',
    chain_id='',
    eip1559_tx=False,
    coin_symbol='OSMO',
    explorer='https://www.mintscan.io/osmosis/',
    explorer_api_abi='',
    api_key=''
)


TON = Network(
    name='TON',
    rpc='',
    chain_id='',
    eip1559_tx=False,
    coin_symbol='TON',
    explorer='https://tonviewer.com/',
    explorer_api_abi='',
    api_key=''
)
