import asyncio
import logging

from dexs.async_get_dex_price import DexPrice


class DexscreenerAggregatorApi(DexPrice):
    async def get_price(self, session):
        logging.info(f"\nSTART {self.name}\n")
        url = f"https://api.dexscreener.com/latest/dex/tokens/{self.src_token},{self.dest_token}"
        try:
            response = await session.get(url)
            logging.info(
                f"\nENTER Print from {self.name}\nreponse.status - {response.status}\n")
            if response.status == 200:
                dexcreener_info = await response.json()
                logging.info(f"\n{self.name} - {dexcreener_info}")
                dexcreener_info = dexcreener_info["pairs"]
                highest_price_pair = None
                highest_price = float('-inf')
                for pair in dexcreener_info:
                    if float(pair["priceUsd"]) > float(highest_price) and pair["baseToken"][
                        "address"] == self.src_token and pair["quoteToken"]["address"] == self.dest_token:
                        highest_price = float(pair["priceUsd"])
                        highest_price_pair = pair
                money_volumes_1h = highest_price * \
                                   float(highest_price_pair['volume']['h1'])
                print(money_volumes_1h)
                if highest_price_pair and money_volumes_1h > 500:
                    data = {"aggregator": self.name,
                            "network": self.network.name,
                            "src_address": self.src_token,
                            "dest_address": self.dest_token,
                            "dex": highest_price_pair["dexId"],
                            "price": highest_price,
                            "data": {
                                "volumes h1": highest_price_pair['volume']['h1']
                            }
                            }
                    logging.info(f"RETURN DATA - {self.name} - {data}")
                    return data
            else:
                logging.info(
                    f"Response status code in DexscreenerAggregatorApi not 200: {response.text}")
        except asyncio.TimeoutError:
            logging.error(
                f"TimeoutError: API call in {self.name} took longer than 10 seconds.")
            return None
        except Exception as e:
            logging.error(
                f"Error in DexscreenerAggregatorApi - get_price, in request of data: {e}")
