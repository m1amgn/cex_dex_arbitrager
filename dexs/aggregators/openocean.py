import asyncio
import logging

from dexs.async_get_dex_price import DexPrice


class OpenoceanAggregatorApi(DexPrice):
    async def get_price(self, session):
        logging.info(f"\nSTART {self.name}\n")
        url_gas = f"https://open-api.openocean.finance/v3/{self.network.chain_id}/gasPrice"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        try:
            response = await session.get(url_gas, headers=headers)
            if response.status == 200:
                gas = await response.json()
                if self.network.chain_id == 1:
                    gas = round(
                        float(gas["without_decimals"]["base"]), 1)
                else:
                    gas = round(
                        float(gas["without_decimals"]["standard"]), 1)
            else:
                logging.info(
                    f"Response status code in OpenoceanAggregatorApi get_gas not 200: {response.text}")
                gas = 35
        except asyncio.TimeoutError:
            logging.error(
                f"TimeoutError: API call in {self.name} took longer than 10 seconds.")
            return None
        except Exception as e:
            logging.error(
                f"Error in OpenoceanAggregatorApi - get_price, in request of gas value: {e}")
            gas = 35
        if gas:
            url = f"https://open-api.openocean.finance/v3/{self.network.chain_id}/quote?inTokenAddress={self.src_token}&outTokenAddress={self.dest_token}&amount={self.amount}&slippage=1&gasPrice={gas}"
        else:
            url = f"https://open-api.openocean.finance/v3/{self.network.chain_id}/quote?inTokenAddress={self.src_token}&outTokenAddress={self.dest_token}&amount={self.amount}&slippage=1&gasPrice=35"
        try:
            response = await session.get(url, headers=headers)
            logging.info(
                f"\nENTER Print from {self.name}\nreponse.status - {response.status}\n")
            if response.status == 200:
                open_ocean_data = await response.json()
                logging.info(f"\n{self.name} - {open_ocean_data}")
                out_amount = open_ocean_data["data"]["outAmount"]
                decimals = open_ocean_data["data"]["outToken"]["decimals"]
                price = float(out_amount) / self.amount / 10 ** decimals
                data = {"aggregator": self.name,
                        "network": self.network.name,
                        "src_address": self.src_token,
                        "dest_address": self.dest_token,
                        "dex": self.name,
                        "price": price,
                        "data": {
                            "estimated gas": open_ocean_data['data']['estimatedGas'],
                            "gas": gas
                        }
                        }
                logging.info(f"RETURN DATA - {self.name} - {data}")
                return data
            else:
                logging.info(
                    f"Response status code in OpenoceanAggregatorApi get data not 200: {response.text}")
        except asyncio.TimeoutError:
            logging.error(
                f"TimeoutError: API call in {self.name} took longer than 10 seconds.")
            return None
        except Exception as e:
            logging.error(
                f"Error in OpenoceanAggregatorApi - get_price, in request of data: {e}")
