import asyncio
import logging

from dexs.async_get_dex_price import DexPrice


class ParaswapAggregatorApi(DexPrice):
    async def get_price(self, session):
        supported_chain_id = [1, 10, 56, 137, 250, 1101, 8453, 42161, 43114]
        if self.network.chain_id in supported_chain_id:
            try:
                logging.info(f"\nSTART {self.name}\n")
                decimals_src_token = await self._get_decimals(self.src_token, session)
                decimals_dest_token = await self._get_decimals(self.dest_token, session)
                url = f"https://api.paraswap.io/prices/?srcToken={self.src_token}&destToken={self.dest_token}&amount={self.amount * 10 ** decimals_src_token}&srcDecimals={decimals_src_token}&destDecimals={decimals_dest_token}&side=SELL&network={self.network.chain_id}"
                response = await session.get(url)
                logging.info(
                    f"\nENTER Print from {self.name}\nreponse.status - {response.status}\n")
                if response.status == 200:
                    paraswap_info = await response.json()
                    logging.info(f"\n{self.name} - {paraswap_info}")
                    paraswap_info = paraswap_info["priceRoute"]
                    data = {"aggregator": self.name,
                            "network": self.network.name,
                            "src_address": self.src_token,
                            "dest_address": self.dest_token,
                            "dex": paraswap_info["bestRoute"][0]["swaps"][0]["swapExchanges"][0]["exchange"],
                            "price": float(paraswap_info["destAmount"]) / 10 ** float(
                                paraswap_info["destDecimals"]) / self.amount,
                            "data": {
                                "fees": paraswap_info["gasCostUSD"]
                            }
                            }
                    logging.info(f"RETURN DATA - {self.name} - {data}")
                    return data
                else:
                    logging.info(
                        f"Response status code in ParaswapAggregatorApi get_price not 200: {response.text}")
            except Exception as e:
                logging.error(
                    f"Error in ParaswapAggregatorApi - get_price, in request of data: {e}")
            except asyncio.TimeoutError:
                logging.error(
                    f"TimeoutError: API call in {self.name} took longer than 10 seconds.")
            return None
        else:
            logging.info(
                f"Aggregator {self.name}: network {self.network.name} not supported.")
