import requests
import json
import os
import sys
import web3
import asyncio
import aiohttp

from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()


class DexPrice:
    if getattr(sys, "frozen", False):
        _ROOT_DIR = Path(sys.executable).parent.absolute()
    else:
        _ROOT_DIR = Path(__file__).parent.parent.absolute()

    _BOT_DIR = os.path.join(_ROOT_DIR, "dexs")
    _DEX_CONTRACTS_PATH = os.path.join(_BOT_DIR, "dex_contracts.json")
    _TOKEN_INFO_PATH = os.path.join(_BOT_DIR, "tokens_info.json")
    _DEFAULT_FACTORY_PATH = os.path.join(_BOT_DIR, "default_factory_abi.json")
    _DEFAULT_V2_POOL_PATH = os.path.join(_BOT_DIR, "default_v2_pool_abi.json")
    _DEFAULT_V3_POOL_PATH = os.path.join(_BOT_DIR, "default_v3_pool_abi.json")
    _dex_contracts = json.load(open(_DEX_CONTRACTS_PATH))
    _tokens_info = json.load(open(_TOKEN_INFO_PATH))

    def __init__(self, src_token: str, dest_token: str, name: str, network, slippage: int | None = 500, amount: int | None = 100):
        self.src_token = src_token
        self.dest_token = dest_token
        self.name = name
        self.network = network
        self.slippage = slippage
        self.amount = amount

        try:
            self.w3 = Web3(Web3.HTTPProvider(self.network.rpc))
            assert self.w3.is_connected(), "w3 is not connected"
        except Exception as e:
            print(f"Error connecting to network: {e}")
            return

    def _get_contract_address_and_abi(self, contract_type: str):
        if contract_type in DexPrice._dex_contracts[self.network.name][self.name]:
            contract_data = DexPrice._dex_contracts[self.network.name][self.name][contract_type]
            return Web3.to_checksum_address(contract_data["address"]), contract_data["abi"]
        else:
            return None, None

    def _get_factory_address(self, router):
        try:
            if self.name == "traderjoe_v2":
                return router.functions.getFactory().call()
            else:
                return router.functions.factory().call()
        except Exception as e:
            print(f"Error in _get_factory_address: {e}")

    def _get_factory_abi(self, factory_address):
        factory_address = Web3.to_checksum_address(factory_address)
        if factory_address != "0x0000000000000000000000000000000000000000":
            try:
                get_factory_abi = requests.get(
                    self.network.explorer_api_abi + factory_address + self.network.api_key).json()
                if get_factory_abi.status_code == 200:
                    return get_factory_abi["result"] if get_factory_abi["result"] != "Invalid Address format" else \
                        json.load(open(DexPrice._DEFAULT_FACTORY_PATH))
                else:
                    print(
                        f"Response code in _get_factory_abi not 200: {get_factory_abi.text}")
            except Exception as e:
                print(
                    f"Error in _get_factory_abi in request of factory abi: {e}")
        else:
            return None

    def _update_contracts_file(self):
        with open(DexPrice._DEX_CONTRACTS_PATH, "w") as file:
            json.dump(DexPrice._dex_contracts, file, indent=4)

    def _get_pool_contract(self):
        if not "pools" in DexPrice._dex_contracts[self.network.name][self.name]:
            pool_abi_path = DexPrice._DEFAULT_V3_POOL_PATH if self.name.split(
                "_")[1] == "v3" else DexPrice._DEFAULT_V2_POOL_PATH
            DexPrice._dex_contracts[self.network.name][self.name].setdefault(
                "pools", {"default_pool_abi": json.load(open(pool_abi_path))})
        pool_key = self.src_token + self.dest_token
        if pool_key in DexPrice._dex_contracts[self.network.name][self.name]["pools"]:
            pool_address = DexPrice._dex_contracts[self.network.name][self.name]["pools"][pool_key]["address"]
            pool_abi = DexPrice._dex_contracts[self.network.name][self.name]["pools"][pool_key]["abi"]
            try:
                return self.w3.eth.contract(address=pool_address, abi=pool_abi)
            except Exception as e:
                print(f"Error in _get_pool_contract: {e}")
        else:
            factory = self._get_factory_contract()
            if factory:
                pool_address = self._get_pool_address(factory)
                pool_abi = self._get_pool_abi(pool_address)
                if pool_abi:
                    DexPrice._dex_contracts[self.network.name][self.name]["pools"].update(
                        {pool_key: {"address": pool_address, "abi": pool_abi}})
                    self._update_contracts_file()
                    try:
                        return self.w3.eth.contract(address=pool_address, abi=pool_abi)
                    except Exception as e:
                        print(f"Error in _get_pool_contract: {e}")
                else:
                    print(
                        f"Pool ABI not available for {self.name} - {pool_address}")
                    return None
            else:
                print("Factory doesn't exist.")
                return None

    def _get_pool_address(self, factory):
        try:
            if self.name == "kyberswap":
                return factory.functions.getPools(Web3.to_checksum_address(self.src_token), Web3.to_checksum_address(self.dest_token)).call()[0]
            elif self.name == "traderjoe_v2":
                return factory.functions.getAllLBPairs(Web3.to_checksum_address(self.src_token), Web3.to_checksum_address(self.dest_token)).call()[0][1]
            elif self.name.split("_")[1] == "v3":
                return factory.functions.getPool(Web3.to_checksum_address(self.src_token), Web3.to_checksum_address(self.dest_token), self.slippage).call()
            else:
                return factory.functions.getPair(Web3.to_checksum_address(self.src_token), Web3.to_checksum_address(self.dest_token)).call()
        except Exception as e:
            print(f"Error in _get_pool_address: {e}")

    async def _get_decimals(self, token_address: str, session):
        token_address = Web3.to_checksum_address(token_address)
        if self.network.name not in DexPrice._tokens_info:
            DexPrice._tokens_info.update({self.network.name: {}})
        if token_address in DexPrice._tokens_info[self.network.name]:
            token_decimals = DexPrice._tokens_info[self.network.name][token_address]["decimals"]
        else:
            url = self.network.explorer_api_abi + token_address + self.network.api_key
            try:
                response = await session.get(url)
                get_token_abi = await response.json()
                if response.status == 200:
                    token_abi = get_token_abi["result"]
                else:
                    print(
                        f"Response code in _get_decimals not 200: {get_token_abi}")
                    token_abi = DexPrice._tokens_info["default_token_abi"]
                if token_abi == "Invalid Address format" or token_abi == "Contract source code not verified" or token_abi == "" or not token_abi:
                    token_abi = DexPrice._tokens_info["default_token_abi"]
            except Exception as e:
                print(f"Error in _get_decimals in request of token_abi: {e}")
                token_abi = DexPrice._tokens_info["default_token_abi"]

            try:
                token_contract = self.w3.eth.contract(
                    address=token_address,
                    abi=token_abi)
                token_symbol = token_contract.functions.symbol().call()
                token_decimals = token_contract.functions.decimals().call()
            except web3.exceptions.ABIFunctionNotFound:
                token_abi = DexPrice._tokens_info["default_token_abi"]
                token_contract = self.w3.eth.contract(
                    address=token_address,
                    abi=token_abi)
                token_symbol = token_contract.functions.symbol().call()
                token_decimals = token_contract.functions.decimals().call()
            DexPrice._tokens_info[self.network.name].update(
                {token_address:
                 {"symbol": token_symbol,
                  "abi": token_abi,
                  "decimals": token_decimals}})
            with open(DexPrice._TOKEN_INFO_PATH, "w") as file:
                json.dump(DexPrice._tokens_info, file, indent=4)
        return int(token_decimals)

    def _get_tokens_symbol(self):
        src_token_symbol = DexPrice._tokens_info[self.network.name][self.src_token]["symbol"]
        dest_token_symbol = DexPrice._tokens_info[self.network.name][self.dest_token]["symbol"]
        return src_token_symbol, dest_token_symbol

    def _get_v2_price(self, pool) -> float:
        try:
            if self.name == "traderjoe_v2":
                reserves = pool.functions.getReservesAndId().call()
            else:
                reserves = pool.functions.getReserves().call()
        except Exception as e:
            print(f"Error in _get_v2_price in request of getReserves: {e}")

        if reserves[0] == 0 or reserves[0] == "" or reserves[1] == 0 or reserves[1] == "":
            print(
                "Something wrong with pool, maybe contract hasn't verified or pool is empty.")
            return None
        else:
            try:
                if self.name == "traderjoe_v2":
                    token0 = pool.functions.tokenX().call()
                    token1 = pool.functions.tokenY().call()
                else:
                    token0 = pool.functions.token0().call()
                    token1 = pool.functions.token1().call()

                if Web3.to_checksum_address(token0) == self.src_token and Web3.to_checksum_address(token1) == self.dest_token:
                    decimals_token0 = self._get_decimals(self.src_token)
                    decimals_token1 = self._get_decimals(self.dest_token)
                    price = (reserves[0] / 10 ** decimals_token0) / \
                            (reserves[1] / 10 ** decimals_token1)
                else:
                    decimals_token0 = self._get_decimals(token0)
                    decimals_token1 = self._get_decimals(token1)
                    price = (reserves[1] / 10 ** decimals_token1) / \
                            (reserves[0] / 10 ** decimals_token0)
                return price
            except Exception as e:
                print(f"Error in _get_v2_price in request of price: {e}")

    def _get_v3_price(self, pool) -> float:
        try:
            slot0 = pool.functions.slot0().call()
            token0 = pool.functions.token0().call()
            token1 = pool.functions.token1().call()
            decimals_token0 = self._get_decimals(token0)
            decimals_token1 = self._get_decimals(token1)
            price_of_token0 = ((slot0[0] / 2 ** 96) ** 2) / \
                (10 ** decimals_token1 / 10 ** decimals_token0)
            if Web3.to_checksum_address(token0) == self.src_token and Web3.to_checksum_address(token1) == self.dest_token:
                return price_of_token0
            else:
                return 1 / price_of_token0
        except Exception as e:
            print(f"Error in _get_v3_price: {e}")

    def _get_aggregator_price(self) -> float:
        try:
            aggregator_contract = self.w3.eth.contract(
                address=DexPrice._dex_contracts[self.network.name][self.name]["oracle"]["address"],
                abi=DexPrice._dex_contracts[self.network.name][self.name]["oracle"]["abi"])
            if self.name == "woofi_aggregator":
                aggregator_price_src_token = aggregator_contract.functions.woPrice(
                    self.src_token).call()
                aggregator_price_dest_token = aggregator_contract.functions.woPrice(
                    self.dest_token).call()
                price_src_token = aggregator_price_src_token[0] / 10 ** 8
                price_dest_token = aggregator_price_dest_token[0] / 10 ** 8
                price = price_src_token / price_dest_token
            else:
                aggregator_price = aggregator_contract.functions.getRate(
                    self.src_token, self.dest_token, False).call()
                decimals_dest_tokens = self._get_decimals(self.dest_token)
                decimals_src_token = self._get_decimals(self.src_token)
                price = aggregator_price / 10 ** decimals_dest_tokens
            return price
        except Exception as e:
            print(f"Error in _get_aggregator_price: {e}")

    def get_price(self):
        if self.name.split("_")[1] == "aggregator":
            price = self._get_aggregator_price()
            src_token_symbol, dest_token_symbol = self._get_tokens_symbol()
            print(
                f"In {self.name} - {self.network.name}: price of {src_token_symbol} in {dest_token_symbol} {price}")
            print("----------------------------------------------")
        else:
            pool = self._get_pool_contract()
            if pool:
                if self.name.split("_")[1] == "v3":
                    price = self._get_v3_price(pool=pool)
                else:
                    price = self._get_v2_price(pool=pool)
                src_token_symbol, dest_token_symbol = self._get_tokens_symbol()
                print(f"Price of {dest_token_symbol} {1 / price}")
                print(f"Price of {src_token_symbol}  {price}")
            else:
                print("Pool doesn't exist.")


class DexscreenerAggregatorApi(DexPrice):
    def __init__(self, src_token: str, dest_token: str, name: str, network, slippage: int | None = 500, amount: int | None = 100):
        super().__init__(src_token, dest_token, name, network, slippage, amount)
        self.name = "Dexscreener"

    async def get_price(self, session):
        print(f"START {self.name}")
        url = f"https://api.dexscreener.com/latest/dex/tokens/{self.src_token},{self.dest_token}"
        try:
            response = await session.get(url)
            dexcreener_info = await response.json()
            print(f"ENTER Print from {self.name}\nreponse.status - {response.status}\n{dexcreener_info}")
            if response.status == 200:
                dexcreener_info = dexcreener_info["pairs"]
                highest_price_pair = None
                highest_price = float('-inf')
                for pair in dexcreener_info:
                    if float(pair["priceNative"]) > float(highest_price) and pair["baseToken"]["address"] == self.src_token:
                        highest_price = pair["priceNative"]
                        highest_price_pair = pair
                money_volumes_1h = int(highest_price_pair["priceNative"] * highest_price_pair['volume']['h1'])
                if highest_price_pair and money_volumes_1h > 100:
                    return {"dex": highest_price_pair["dexId"],
                            "price": highest_price_pair["priceNative"],
                            "data": {
                                "deals": highest_price_pair["txns"],
                                "volumes": highest_price_pair['volume']
                            }
                    }
            else:
                print(
                    f"Response status code in DexscreenerAggregatorApi not 200: {response.text}")
        except Exception as e:
            print(
                f"Error in DexscreenerAggregatorApi - get_price, in request of data: {e}")


class ParaswapAggregatorApi(DexPrice):
    def __init__(self, src_token: str, dest_token: str, name: str, network, slippage: int | None = 500, amount: int | None = 100):
        super().__init__(src_token, dest_token, name, network, slippage, amount)
        self.name = "Paraswap"

    async def get_price(self, session):
        print(f"START {self.name}")
        decimals_src_token = await self._get_decimals(self.src_token, session)
        decimals_dest_token = await self._get_decimals(self.dest_token, session)
        url = f"https://apiv5.paraswap.io/prices/?srcToken={self.src_token}&destToken={self.dest_token}&amount={self.amount*10**decimals_src_token}&srcDecimals={decimals_src_token}&destDecimals={decimals_dest_token}&side=SELL&network={self.network.chain_id}"
        try:
            response = await session.get(url)
            paraswap_info = await response.json()
            print(f"ENTER Print from {self.name}\nreponse.status - {response.status}\n{paraswap_info}")
            if response.status == 200:
                paraswap_info = paraswap_info["priceRoute"]
                return {"dex": paraswap_info["bestRoute"][0]["swaps"][0]["swapExchanges"][0]["exchange"],
                        "price": float(paraswap_info["destAmount"])/10**float(paraswap_info["destDecimals"]) / self.amount,
                        "data": {
                            "fees": paraswap_info["gasCostUSD"]
                }
                }
            else:
                print(
                    f"Response status code in ParaswapAggregatorApi get_price not 200: {response.text}")
        except Exception as e:
            print(
                f"Error in ParaswapAggregatorApi - get_price, in request of data: {e}")


class KyberswapAggregatorApi(DexPrice):
    def __init__(self, src_token: str, dest_token: str, name: str, network, slippage: int | None = 500, amount: int | None = 100):
        super().__init__(src_token, dest_token, name, network, slippage, amount)
        self.name = "Kyberswap"

    async def get_price(self, session):
        print(f"START {self.name}")
        decimals_src_token = await self._get_decimals(self.src_token, session)
        decimals_dest_token = await self._get_decimals(self.dest_token, session)
        if self.network.name == "BNB Smart Chain (BEP20)":
            network = "bsc"
        elif self.network.name == "Avalanche C-Chain":
            network = "avalanche"
        else:
            network = self.network.name

        url = f"https://aggregator-api.kyberswap.com/{network.lower()}/route/encode?tokenIn={self.src_token}&tokenOut={self.dest_token}&amountIn={self.amount*10**decimals_src_token}&to=0x0000000000000000000000000000000000000000&saveGas=0&gasInclude=1&slippageTolerance=50"
        try:
            response = await session.get(url)
            kyberswap_info = await response.json()
            print(f"ENTER Print from {self.name}\nreponse.status - {response.status}\n{kyberswap_info}")
            if response.status == 200:
                kyberswap_data_list = []
                for swaps in kyberswap_info["swaps"]:
                    for swap in swaps:
                        if Web3.to_checksum_address(swap["tokenIn"]) == Web3.to_checksum_address(self.src_token) and Web3.to_checksum_address(swap["tokenOut"]) == Web3.to_checksum_address(self.dest_token):
                            kyberswap_data_list.append({"dex": swap["exchange"],
                                                        "price": (float(swap["amountOut"])/10**decimals_dest_token) / (float(swap["swapAmount"])/10**decimals_src_token) / self.amount,
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
                return highest_price_dex
            else:
                print(
                    f"Response status code in KyberswapAggregatorApi not 200: {response.text}")
        except Exception as e:
            print(
                f"Error in KyberswapAggregatorApi - get_price, in request of data: {e}")


class OpenoceanAggregatorApi(DexPrice):
    def __init__(self, src_token: str, dest_token: str, name: str, network, slippage: int | None = 500, amount: int | None = 100):
        super().__init__(src_token, dest_token, name, network, slippage, amount)
        self.name = "OpenOcean"

    async def get_price(self, session):
        print(f"START {self.name}")
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
            gas = await response.json()
            if response.status == 200:
                if self.network.chain_id == 1:
                    gas = round(
                        float(gas["without_decimals"]["base"]), 1)
                else:
                    gas = round(
                        float(gas["without_decimals"]["standard"]), 1)
            else:
                print(
                    f"Response status code in OpenoceanAggregatorApi get_gas not 200: {response.text}")
                gas = 35
        except Exception as e:
            print(
                f"Error in OpenoceanAggregatorApi - get_price, in request of gas value: {e}")
            gas = 35
        if gas:
            url = f"https://open-api.openocean.finance/v3/{self.network.chain_id}/quote?inTokenAddress={self.src_token}&outTokenAddress={self.dest_token}&amount={self.amount}&slippage=1&gasPrice={gas}"
        else:
            url = f"https://open-api.openocean.finance/v3/{self.network.chain_id}/quote?inTokenAddress={self.src_token}&outTokenAddress={self.dest_token}&amount={self.amount}&slippage=1&gasPrice=35"
        try:
            response = await session.get(url, headers=headers)
            print(f'OpenOcean response - {response}')
            open_ocean_data = await response.json()
            print(f'OpenOcean data - {open_ocean_data}')
            print(f"ENTER Print from {self.name}\nreponse.status - {response.status}\n{open_ocean_data}")
            if response.status == 200:
                out_amount = open_ocean_data["data"]["outAmount"]
                decimals = open_ocean_data["data"]["outToken"]["decimals"]
                price = float(out_amount) / self.amount / 10 ** decimals
                return {"dex": self.name,
                        "price": price,
                        "data": {
                            "estimated gas": open_ocean_data['data']['estimatedGas'],
                            "gas": gas
                        }
                        }
            else:
                print(
                    f"Response status code in OpenoceanAggregatorApi get data not 200: {response.text}")
        except Exception as e:
            print(
                f"Error in OpenoceanAggregatorApi - get_price, in request of data: {e}")


class OneInchAggregatorApi(DexPrice):
    def __init__(self, src_token: str, dest_token: str, name: str, network, slippage: int | None = 500, amount: int | None = 100):
        super().__init__(src_token, dest_token, name, network, slippage, amount)
        self.name = "1inch"

    async def get_price(self, session):
        print(f"START {self.name}")
        decimals_src_token = await self._get_decimals(self.src_token, session)
        decimals_dest_token = await self._get_decimals(self.dest_token, session)
        url = f"https://api.1inch.dev/swap/v5.2/{self.network.chain_id}/quote"
        headers = {
            "Authorization": os.getenv('ONE_INCH_BEARER_TOKEN')
        }
        params = {
            "src": self.src_token,
            "dst": self.dest_token,
            "amount": self.amount*10**decimals_src_token
        }
        try:
            response = await session.get(url, headers=headers, params=params)
            one_inch_data = await response.json()
            print(f"ENTER Print from {self.name}\nreponse.status - {response.status}\n{one_inch_data}")
            if response.status == 200:
                return {"dex": self.name,
                        "price": int(one_inch_data["toAmount"]) / 10 ** decimals_dest_token / self.amount}
            else:
                print(
                    f"Response status code in OneInchAggregatorApi get_price not 200: {response.text}")
        except Exception as e:
            print(
                f"Error in OneInchAggregatorApi - get_price, in request of data: {e}")
