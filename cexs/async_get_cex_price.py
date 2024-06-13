import asyncio
import aiohttp


class CexPrice:
    def __init__(self, exchange):
        self.exchange = exchange
        self.pair = self.exchange.prepare_pair()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

    async def get_exchange_data(self, session) -> dict:
        print(f"START {self.exchange.name}")
        url = self.exchange.url
        if "symbol" in url:
            symbol_url = self.pair
            url = url.replace("symbol", symbol_url)
            if self.exchange.params != "":
                response = await session.get(url, headers=self.headers, params=self.exchange.params)
            else:
                response = await session.get(url, headers=self.headers)
        else:
            params = self.exchange.params
            for key, value in params.items():
                if key == "symbol" or key == "instrument_name" or key == "market" or key == "pair" or key == "instId":
                    value = self.pair
                    params.update({key: value})
            response = await session.get(url, headers=self.headers, params=params)
        print(f"response {self.exchange.name} - {response}")
        data = await response.json()
        print(f"data {self.exchange.name} - {data}")
        print(
            f"ENTER Print from CexPrice get_exchange data\nreponse.status - {response.status}\n{data}\n{self.exchange.name}")

        if response.status == 200:
            data = await response.json()
            print(
                f"ENTER Print from CexPrice get_exchange data\nreponse.status - {response.status}\n{data}\n{self.exchange.name}")
            return data
        else:
            print(
                f"Something went wrong with fetch data: {data}\nWith exchange: {self.exchange.name}")
            return None

    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["bids"]
                asks = data["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class BybitPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["result"]["b"]
                asks = data["result"]["a"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class BingxPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["data"]["bids"]
                asks = data["data"]["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[-1][0])
                asks_volumes = float(asks[-1][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class BitfinexGeminiPrice(CexPrice):
    async def get_price(self, session) -> dict:
        '''
        Get price from Bitfinex, Gemini
        '''
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["bids"]
                asks = data["asks"]

                max_bids_price = float(bids[0]["price"])
                bids_volumes = float(bids[0]["amount"])
                min_asks_price = float(asks[0]["price"])
                asks_volumes = float(asks[0]["amount"])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class BitgetCoinwKucoinPrice(CexPrice):
    async def get_price(self, session) -> dict:
        '''
        Get price from Bitget, Coinw, Kucoin
        '''
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["data"]["bids"]
                asks = data["data"]["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class BitmexPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data[1]
                asks = data[0]

                assets_url = "https://www.bitmex.com/api/v1/wallet/assets"

                response = await session.get(assets_url)
                assets_data = await response.json()

                if response.status == 200:
                    for currency in assets_data:
                        if bids["side"] == "Buy":
                            max_bids_price = float(bids["price"])
                            if currency["asset"] in self.pair and currency["asset"] != "USDT":
                                bids_volumes = float(
                                    bids["size"] / 10 ** currency["scale"])
                        if asks["side"] == "Sell":
                            min_asks_price = float(asks["price"])
                            if currency["asset"] in self.pair and currency["asset"] != "USDT":
                                asks_volumes = float(
                                    asks["size"] / 10 ** currency["scale"])

                    crypto_data = {
                        "pair": self.pair,
                        "max_bids_price": max_bids_price,
                        "bids_volumes": bids_volumes,
                        "min_asks_price": min_asks_price,
                        "asks_volumes": asks_volumes
                    }

                    return crypto_data
                else:
                    print(
                        f"Something went wrong with fetch data: {response.text}")
                    return None
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class BittrexPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["bid"]
                asks = data["ask"]

                max_bids_price = float(bids[0]["rate"])
                bids_volumes = float(bids[0]["quantity"])
                min_asks_price = float(asks[0]["rate"])
                asks_volumes = float(asks[0]["quantity"])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class CryptocomPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["result"]["data"][0]["bids"]
                asks = data["result"]["data"][0]["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class DeribitPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["result"]["bids"]
                asks = data["result"]["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class DydxPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["bids"]
                asks = data["asks"]

                max_bids_price = float(bids[0]["price"])
                bids_volumes = float(bids[0]["size"])
                min_asks_price = float(asks[0]["price"])
                asks_volumes = float(asks[0]["size"])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class GarantexPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["bids"]
                asks = data["asks"]

                max_bids_price = float(bids[0]["price"])
                bids_volumes = float(bids[0]["volume"])
                min_asks_price = float(asks[0]["price"])
                asks_volumes = float(asks[0]["volume"])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class HuobiPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["tick"]["bids"]
                asks = data["tick"]["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class KinePrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                price = float(data["data"]["price"])

                crypto_data = {
                    "pair": self.pair,
                    "price": price,
                }

                return crypto_data
            else:
                print("No data.")
        except Exception as e:
            print(e)


class KrakenPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["result"][self.pair]["bids"]
                asks = data["result"][self.pair]["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class OkxPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["data"][0]["bids"]
                asks = data["data"][0]["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class PhemexPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["result"]["book"]["bids"]
                asks = data["result"]["book"]["asks"]

                max_bids_price = float(bids[0][0] / 10000)
                bids_volumes = float(bids[0][1] / 10000)
                min_asks_price = float(asks[0][0] / 10000)
                asks_volumes = float(asks[0][1] / 10000)

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class PoloniexPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["bids"]
                asks = data["asks"]

                max_bids_price = float(bids[0])
                bids_volumes = float(bids[1])
                min_asks_price = float(asks[0])
                asks_volumes = float(asks[1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class YoubitPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data[self.pair]["bids"]
                asks = data[self.pair]["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class CoinexPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["data"]["depth"]["bids"]
                asks = data["data"]["depth"]["asks"]

                max_bids_price = float(bids[0][0])
                bids_volumes = float(bids[0][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)


class BackpackPrice(CexPrice):
    async def get_price(self, session) -> dict:
        try:
            data = await self.get_exchange_data(session)
            if data:
                bids = data["bids"]
                asks = data["asks"]

                max_bids_price = float(bids[-1][0])
                bids_volumes = float(bids[-1][1])
                min_asks_price = float(asks[0][0])
                asks_volumes = float(asks[0][1])

                crypto_data = {
                    "pair": self.pair,
                    "max_bids_price": max_bids_price,
                    "bids_volumes": bids_volumes,
                    "min_asks_price": min_asks_price,
                    "asks_volumes": asks_volumes
                }

                return crypto_data
            else:
                print("No data.")
                return None
        except Exception as e:
            print(e)
