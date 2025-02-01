import asyncio
import logging

from web3 import Web3

from dexs.async_get_dex_price import DexPrice


class KyberswapAggregatorApi(DexPrice):
    async def get_price(self, session):
        supported_network = ['ethereum',
                             'bsc',
                             'arbitrum',
                             'polygon',
                             'optimism',
                             'avalanche',
                             'base',
                             'cronos',
                             'zksync',
                             'fantom',
                             'linea',
                             'polygon-zkevm',
                             'aurora',
                             'bittorent',
                             'scroll']

        if self.network.name == "BNB Smart Chain (BEP20)":
            network = "bsc"
        elif self.network.name == "Avalanche C-Chain":
            network = "avalanche"
        else:
            network = self.network.name

        if network.lower() in supported_network:
            try:
                logging.info(f"\nSTART {self.name}\n")
                decimals_src_token = await self._get_decimals(self.src_token, session)
                decimals_dest_token = await self._get_decimals(self.dest_token, session)

                url = f"https://aggregator-api.kyberswap.com/{network.lower()}/route/encode?tokenIn={self.src_token}&tokenOut={self.dest_token}&amountIn={self.amount * 10 ** decimals_src_token}&to=0x0000000000000000000000000000000000000000&saveGas=0&gasInclude=1&slippageTolerance=50"
                response = await session.get(url)
                logging.info(
                    f"\nENTER Print from {self.name}\nreponse.status - {response.status}\n")
                if response.status == 200:
                    kyberswap_info = await response.json()
                    logging.info(f"\n{self.name} - {kyberswap_info}")
                    kyberswap_data_list = []
                    for swaps in kyberswap_info["swaps"]:
                        for swap in swaps:
                            if Web3.to_checksum_address(swap["tokenIn"]) == Web3.to_checksum_address(
                                    self.src_token) and Web3.to_checksum_address(
                                    swap["tokenOut"]) == Web3.to_checksum_address(self.dest_token):
                                kyberswap_data_list.append({"aggregator": self.name,
                                                            "network": self.network.name,
                                                            "src_address": self.src_token,
                                                            "dest_address": self.dest_token,
                                                            "dex": swap["exchange"],
                                                            "price": (float(
                                                                swap["amountOut"]) / 10 ** decimals_dest_token) / (
                                                                                 float(swap[
                                                                                           "swapAmount"]) / 10 ** decimals_src_token) / self.amount,
                                                            "data": {
                                                                "fees": swap["poolExtra"],
                                                                "gas": kyberswap_info["gasUsd"]}
                                                            })
                    highest_price_dex = {}
                    highest_price = float("-inf")
                    for dex in kyberswap_data_list:
                        if dex["price"] > highest_price:
                            highest_price = dex["price"]
                            highest_price_dex.update(dex)
                    logging.info(
                        f"RETURN DATA - {self.name} - {highest_price_dex}")
                    return highest_price_dex
                else:
                    logging.info(
                        f"Response status code in KyberswapAggregatorApi not 200: {response.text}")
            except Exception as e:
                logging.error(
                    f"Error in KyberswapAggregatorApi - get_price, in request of data: {e}")
            except asyncio.TimeoutError:
                logging.error(
                    f"TimeoutError: API call in {self.name} took longer than 10 seconds.")
            return None
        else:
            logging.info(
                f"Aggregator {self.name}: network {self.network.name} not supported.")
