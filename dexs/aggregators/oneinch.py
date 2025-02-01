import asyncio
import logging
import os

from dexs.async_get_dex_price import DexPrice


class OneInchAggregatorApi(DexPrice):
    async def get_price(self, session):
        try:
            logging.info(f"\nSTART {self.name}\n")
            decimals_src_token = await self._get_decimals(self.src_token, session)
            decimals_dest_token = await self._get_decimals(self.dest_token, session)
            url = f"https://api.1inch.dev/swap/v5.2/{self.network.chain_id}/quote"
            headers = {
                "Authorization": os.getenv('ONE_INCH_BEARER_TOKEN')
            }
            params = {
                "src": self.src_token,
                "dst": self.dest_token,
                "amount": self.amount * 10 ** decimals_src_token
            }
            response = await session.get(url, headers=headers, params=params)
            logging.info(
                f"\nENTER Print from {self.name}\nreponse.status - {response.status}\n")
            if response.status == 200:
                one_inch_data = await response.json()
                logging.info(f"\n{self.name} - {one_inch_data}")
                data = {"aggregator": self.name,
                        "network": self.network.name,
                        "src_address": self.src_token,
                        "dest_address": self.dest_token,
                        "dex": self.name,
                        "price": int(one_inch_data["toAmount"]) / 10 ** decimals_dest_token / self.amount
                        }
                logging.info(f"RETURN DATA - {self.name} - {data}")
                return data
            else:
                logging.info(
                    f"Response status code in OneInchAggregatorApi get_price not 200: {response.text}")
        except asyncio.TimeoutError:
            logging.error(
                f"TimeoutError: API call in {self.name} took longer than 10 seconds.")
            return None
        except Exception as e:
            logging.error(
                f"Error in OneInchAggregatorApi - get_price, in request of data: {e}")
