import asyncio
import logging

from dexs.async_get_dex_price import DexPrice


class StonFiApi(DexPrice):
    async def get_price(self, session):
        supported_network = ['TON']
        print(f"NETWORK - {self.network.name}")
        if self.network.name in supported_network:
            logging.info(f"\nSTART {self.name}\n")
            url = f"https://api.ston.fi/v1/assets/{self.src_token}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            try:
                response = await session.get(url, headers=headers)
                logging.info(
                    f"\nENTER Print from {self.name}\nreponse.status - {response.status}\n")
                if response.status == 200:
                    stonfi_data = await response.json()
                    logging.info(f"\n{self.name} - {stonfi_data}")
                    data = {"aggregator": self.name,
                            "network": self.network.name,
                            "src_address": self.src_token,
                            "dest_address": self.dest_token,
                            "dex": self.name,
                            "price": float(stonfi_data['asset']['dex_price_usd'])
                            }
                    logging.info(f"RETURN DATA - {self.name} - {data}")
                    return data
                else:
                    logging.info(
                        f"Response status code in StonFiApi get_price not 200: {response.text}")
            except asyncio.TimeoutError:
                logging.error(
                    f"TimeoutError: API call in {self.name} took longer than 10 seconds.")
                return None
            except Exception as e:
                logging.error(
                    f"Error in StonFiApi - get_price, in request of data: {e}")
        else:
            logging.info(
                f"Aggregator {self.name}: network {self.network.name} not supported.")
