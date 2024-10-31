class CexExchanges:
    '''Bybit, Binance, Mexc'''

    def __init__(self,
                 name: str,
                 url: str,
                 params: dict,
                 src_token: str,
                 dest_token: str):
        self.name = name
        self.url = url
        self.params = params
        self.src_token = src_token
        self.dest_token = dest_token

    def prepare_pair(self) -> str:
        pairs = (self.src_token+self.dest_token).upper()
        return pairs


class BingxBittrexCoinbaseKucoinOkxCexio(CexExchanges):
    '''Bingx, Bittrex, Coinbase, Kucoin, Okx, Cexio'''

    def prepare_pair(self) -> str:
        pairs = (self.src_token+"-"+self.dest_token).upper()
        return pairs


class BitfinexKinePhemex(CexExchanges):
    '''Bitfinex, Kine, Phemex'''

    def prepare_pair(self) -> str:
        if self.src_token == "USDT":
            self.src_token = "USD"
        if self.dest_token == "USDT":
            self.dest_token = "USD"
        pairs = (self.src_token+self.dest_token).upper()
        return pairs


class BitgetYoubitLbank(CexExchanges):
    '''Bitget, Youbit, Lbank'''

    def prepare_pair(self) -> str:
        pairs = (self.src_token+"_"+self.dest_token).lower()
        return pairs


class BitmexKraken(CexExchanges):
    '''Bitmex, Kraken'''

    def prepare_pair(self) -> str:
        if self.src_token == "BTC":
            self.src_token = "XBT"
        if self.dest_token == "BTC":
            self.dest_token = "XBT"
        pairs = (self.src_token+self.dest_token).upper()
        return pairs


class BitstampGarantexHuobi(CexExchanges):
    '''Bitstamp, Garantex, Huobi'''

    def prepare_pair(self) -> str:
        pairs = (self.src_token+self.dest_token).lower()
        return pairs


class CoinwCryptocomPoloniexBackpackGateio(CexExchanges):
    '''Coinw, Cryptocom, Poloniex, Backpack, Gateio'''

    def prepare_pair(self) -> str:
        pairs = (self.src_token+"_"+self.dest_token).upper()
        return pairs


class Deribit(CexExchanges):
    '''Deribit'''

    def prepare_pair(self) -> str:
        if self.src_token == "USDT":
            self.src_token = "PERPETUAL"
        if self.dest_token == "USDT":
            self.dest_token = "PERPETUAL"
        pairs = (self.src_token+"-"+self.dest_token).upper()
        return pairs


class Dydx(CexExchanges):
    '''Dydx'''

    def prepare_pair(self) -> str:
        if self.src_token == "USDT":
            self.src_token = "USD"
        if self.dest_token == "USDT":
            self.dest_token = "USD"
        pairs = (self.src_token+"-"+self.dest_token).upper()
        return pairs


class Gemini(CexExchanges):
    '''Gemini'''

    def prepare_pair(self) -> str:
        if self.src_token == "USDT":
            self.src_token = "USD"
        if self.dest_token == "USDT":
            self.dest_token = "USD"
        pairs = (self.src_token+self.dest_token).lower()
        return pairs


class Zigzag(CexExchanges):
    '''Zigzag'''

    def prepare_pair(self) -> str:
        if self.src_token == "BTC":
            self.src_token = "WBTC"
        if self.dest_token == "BTC":
            self.dest_token = "WBTC"
        pairs = (self.src_token+"-"+self.dest_token).lower()
        return pairs


Bybit_exchange = CexExchanges(
    name="bybit",
    url="https://api.bybit.com/v5/market/orderbook",
    params={
        "category": "spot",
        "symbol": "",
    },
    src_token="",
    dest_token="",
)


Binance_exchange = CexExchanges(
    name="binance",
    url="https://api.binance.com/api/v3/depth",
    params={
        "symbol": "",
        "limit": 1
    },
    src_token="",
    dest_token=""
)


Bingx_exchange = BingxBittrexCoinbaseKucoinOkxCexio(
    name="bingx",
    url="https://open-api.bingx.com/openApi/spot/v1/market/depth",
    params={
        "symbol": "",
        "limit": 100
    },
    src_token="",
    dest_token="",
)


Bitfinex_exchange = BitfinexKinePhemex(
    name="bitfinex",
    url="https://api.bitfinex.com/v1/book/symbol",
    params="",
    src_token="",
    dest_token="",
)


Bitget_exchange = BitgetYoubitLbank(
    name="bitget",
    url="https://api.bitget.com/data/v1/market/depth",
    params={
        "symbol": ""
    },
    src_token="",
    dest_token="",
)


Bitmex_exchange = BitmexKraken(
    name="bitmex",
    url="https://www.bitmex.com/api/v1/orderBook/L2",
    params={
        "symbol": "",
        "depth": 1
    },
    src_token="",
    dest_token="",
)


Bitstamp_exchange = BitstampGarantexHuobi(
    name="bitstamp",
    url="https://www.bitstamp.net/api/v2/order_book/symbol",
    params="",
    src_token="",
    dest_token="",
)


Bittrex_exchange = BingxBittrexCoinbaseKucoinOkxCexio(
    name="bittrex",
    url="https://api.bittrex.com/v3/markets/symbol/orderbook",
    params={
        "depth": 1
    },
    src_token="",
    dest_token="",
)


Coinbase_exchange = BingxBittrexCoinbaseKucoinOkxCexio(
    name="coinbase",
    url="https://api.exchange.coinbase.com/products/symbol/book",
    params="",
    src_token="",
    dest_token="",
)


Coinw_exchange = CoinwCryptocomPoloniexBackpackGateio(
    name="coinw",
    url="https://api.coinw.com/api/v1/public",
    params={
        "command": "returnOrderBook",
        "symbol": "",
        "limit": 20
    },
    src_token="",
    dest_token="",
)


Cryptocom_exchange = CoinwCryptocomPoloniexBackpackGateio(
    name="cryptocom",
    url="https://api.crypto.com/v2/public/get-book",
    params={
        "instrument_name": "",
        "depth": 5
    },
    src_token="",
    dest_token="",
)


Deribit_exchange = Deribit(
    name="deribit",
    url="https://www.deribit.com/api/v2/public/get_order_book",
    params={
        "instrument_name": "",
        "depth": 5
    },
    src_token="",
    dest_token="",
)


Dydx_exchange = Dydx(
    name="dydx",
    url="https://api.dydx.exchange/v3/orderbook/symbol",
    params="",
    src_token="",
    dest_token="",
)


Garantex_exchange = BitstampGarantexHuobi(
    name="garantex",
    url="https://garantex.org/api/v2/depth",
    params={
        "market": ""
    },
    src_token="",
    dest_token="",
)


Gateio_exchange = CoinwCryptocomPoloniexBackpackGateio(
    name="gateio",
    url="https://api.gateio.ws/api/v4/spot/order_book",
    params={
        "currency_pair": ""
        },
    src_token="",
    dest_token="",
)


Gemini_exchange = Gemini(
    name="gemini",
    url="https://api.gemini.com/v1/book/symbol",
    params="",
    src_token="",
    dest_token="",
)


Huobi_exchange = BitstampGarantexHuobi(
    name="huobi",
    url="https://api.huobi.pro/market/depth",
    params={
        "symbol": "",
        "type": "step1",
        "depth": 5
    },
    src_token="",
    dest_token="",
)


Kine_exchange = BitfinexKinePhemex(
    name="kine",
    url="https://api.kine.exchange/market/api/price/symbol",
    params="",
    src_token="",
    dest_token="",
)


Kraken_exchange = BitmexKraken(
    name="kraken",
    url="https://api.kraken.com/0/public/Depth",
    params={
        "pair": "",
        "count": 1
    },
    src_token="",
    dest_token=""
)


Kucoin_exchange = BingxBittrexCoinbaseKucoinOkxCexio(
    name="kucoin",
    url="https://api.kucoin.com/api/v1/market/orderbook/level2_20",
    params={
        "symbol": "",
        "limit": 1
    },
    src_token="",
    dest_token="",
)


Mexc_exchange = CexExchanges(
    name="mexc",
    url="https://api.mexc.com/api/v3/depth",
    params={
        "symbol": "",
        "limit": 5
    },
    src_token="",
    dest_token="",
)


Okx_exchange = BingxBittrexCoinbaseKucoinOkxCexio(
    name="okx",
    url="https://www.okx.com/api/v5/market/books",
    params={
        "instId": "",
        "sz": 5
    },
    src_token="",
    dest_token="",
)


Phemex_exchange = BitfinexKinePhemex(
    name="phemex",
    url="https://api.phemex.com/md/orderbook",
    params={
        "symbol": ""
    },
    src_token="",
    dest_token="",
)


Poloniex_exchange = CoinwCryptocomPoloniexBackpackGateio(
    name="poloniex",
    url="https://api.poloniex.com/markets/symbol/orderBook",
    params="",
    src_token="",
    dest_token="",
)


Youbit_exchange = BitgetYoubitLbank(
    name="youbit",
    url="https://yobit.net/api/3/depth/symbol",
    params={
        "limit": 5
    },
    src_token="",
    dest_token="",
)


Zigzag_exchange = Zigzag(
    name="zigzag",
    url="https://zigzag-exchange.herokuapp.com/api/coinmarketcap/v1/orderbook/symbol/1",
    params="",
    src_token="",
    dest_token="",
)


Coinex_exchange = CexExchanges(
    name="coinex",
    url="https://api.coinex.com/v2/spot/depth",
    params={
        "market": "",
        "limit": 50,
        "interval": 0
    },
    src_token="",
    dest_token="",
)


Backpack_exchange = CoinwCryptocomPoloniexBackpackGateio(
    name="backpack",
    url="https://api.backpack.exchange/api/v1/depth",
    params={
        "symbol": ""
    },
    src_token="",
    dest_token="",
)


Cexio_exchange = BingxBittrexCoinbaseKucoinOkxCexio(
    name="cexio",
    url="https://trade.cex.io/api/spot/rest-public/get_order_book",
    params={
        "pair": "",
    },
    src_token="",
    dest_token="",
)

Lbank_exchange = BitgetYoubitLbank(
    name="lbank",
    url="https://api.lbank.info/v2/depth.do", #https://www.lbkex.net/v2/depth.do, https://api.lbkex.com/v2/depth.do
    params={
        "symbol": "",
        "size": 50
    },
    src_token="",
    dest_token="",
)