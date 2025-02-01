import asyncio
import logging
import os
import sys
from pathlib import Path

import requests
import ujson as json
import web3
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
logging.basicConfig(level=logging.INFO)


class DexPrice:
    if getattr(sys, "frozen", False):
        _ROOT_DIR = Path(sys.executable).parent.absolute()
    else:
        _ROOT_DIR = Path(__file__).parent.parent.absolute()

    _BOT_DIR = os.path.join(_ROOT_DIR, "dexs")
    _DEX_CONTRACTS_PATH = os.path.join(_BOT_DIR, "abi/dex_contracts.json")
    _TOKEN_INFO_PATH = os.path.join(_BOT_DIR, "abi/tokens_info.json")
    _DEFAULT_FACTORY_PATH = os.path.join(_BOT_DIR, "abi/default_factory_abi.json")
    _DEFAULT_V2_POOL_PATH = os.path.join(_BOT_DIR, "abi/default_v2_pool_abi.json")
    _DEFAULT_V3_POOL_PATH = os.path.join(_BOT_DIR, "abi/default_v3_pool_abi.json")
    _dex_contracts = json.load(open(_DEX_CONTRACTS_PATH))
    _tokens_info = json.load(open(_TOKEN_INFO_PATH))

    def __init__(self, src_token: str, dest_token: str, name: str, network, slippage: int | None = 500,
                 amount: int | None = 1):
        self.src_token = src_token
        self.dest_token = dest_token
        self.name = name
        self.network = network
        self.slippage = slippage
        self.amount = amount

        if self.network.name not in ['Solana', 'Osmosis', 'TON']:
            self.src_token = Web3.to_checksum_address(self.src_token)
            self.dest_token = Web3.to_checksum_address(self.dest_token)

    def _connect_web3(self):
        try:
            w3 = Web3(Web3.HTTPProvider(self.network.rpc))
            return w3
        except Exception as e:
            logging.error(f"Error connecting to web3: {e}")

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
            logging.error(f"Error in _get_factory_address: {e}")

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
                    logging.info(
                        f"Response code in _get_factory_abi not 200: {get_factory_abi.text}")
            except Exception as e:
                logging.error(
                    f"Error in _get_factory_abi in request of factory abi: {e}")
        else:
            return None

    def _update_contracts_file(self):
        with open(DexPrice._DEX_CONTRACTS_PATH, "w") as file:
            json.dump(DexPrice._dex_contracts, file, indent=4)

    def _get_pool_contract(self):
        w3 = self._connect_web3()
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
                return w3.eth.contract(address=pool_address, abi=pool_abi)
            except Exception as e:
                logging.error(f"Error in _get_pool_contract: {e}")
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
                        return w3.eth.contract(address=pool_address, abi=pool_abi)
                    except Exception as e:
                        logging.error(f"Error in _get_pool_contract: {e}")
                else:
                    logging.info(
                        f"Pool ABI is not available for {self.name} - {pool_address}")
                    return None
            else:
                logging.info("Factory doesn't exist.")
                return None

    def _get_pool_address(self, factory):
        try:
            if self.name == "kyberswap":
                return factory.functions.getPools(Web3.to_checksum_address(self.src_token),
                                                  Web3.to_checksum_address(self.dest_token)).call()[0]
            elif self.name == "traderjoe_v2":
                return factory.functions.getAllLBPairs(Web3.to_checksum_address(self.src_token),
                                                       Web3.to_checksum_address(self.dest_token)).call()[0][1]
            elif self.name.split("_")[1] == "v3":
                return factory.functions.getPool(Web3.to_checksum_address(self.src_token),
                                                 Web3.to_checksum_address(self.dest_token), self.slippage).call()
            else:
                return factory.functions.getPair(Web3.to_checksum_address(self.src_token),
                                                 Web3.to_checksum_address(self.dest_token)).call()
        except Exception as e:
            logging.error(f"Error in _get_pool_address: {e}")

    async def _get_decimals(self, token_address: str, session):
        w3 = self._connect_web3()
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
                    logging.info(
                        f"Response code in _get_decimals not 200: {get_token_abi}")
                    token_abi = DexPrice._tokens_info["default_token_abi"]
                if token_abi == "Invalid Address format" or token_abi == "Contract source code not verified" or token_abi == "" or not token_abi:
                    token_abi = DexPrice._tokens_info["default_token_abi"]
            except asyncio.TimeoutError:
                logging.error(
                    f"TimeoutError: API call in {self.name} took longer than 10 seconds.")
                token_abi = DexPrice._tokens_info["default_token_abi"]
            except Exception as e:
                logging.error(
                    f"Error in _get_decimals in request of token_abi: {e}")
                token_abi = DexPrice._tokens_info["default_token_abi"]

            try:
                token_contract = w3.eth.contract(
                    address=token_address,
                    abi=token_abi)
                token_symbol = token_contract.functions.symbol().call()
                token_decimals = token_contract.functions.decimals().call()
            except asyncio.TimeoutError:
                logging.error(
                    f"TimeoutError: API call in {self.name} took longer than 10 seconds.")
                token_abi = DexPrice._tokens_info["default_token_abi"]
                token_contract = w3.eth.contract(
                    address=token_address,
                    abi=token_abi)
                token_symbol = token_contract.functions.symbol().call()
                token_decimals = token_contract.functions.decimals().call()
            except web3.exceptions.ABIFunctionNotFound:
                token_abi = DexPrice._tokens_info["default_token_abi"]
                token_contract = w3.eth.contract(
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
            logging.error(
                f"Error in _get_v2_price in request of getReserves: {e}")

        if reserves[0] == 0 or reserves[0] == "" or reserves[1] == 0 or reserves[1] == "":
            logging.info(
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

                if Web3.to_checksum_address(token0) == self.src_token and Web3.to_checksum_address(
                        token1) == self.dest_token:
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
                logging.error(
                    f"Error in _get_v2_price in request of price: {e}")

    def _get_v3_price(self, pool) -> float:
        try:
            slot0 = pool.functions.slot0().call()
            token0 = pool.functions.token0().call()
            token1 = pool.functions.token1().call()
            decimals_token0 = self._get_decimals(token0)
            decimals_token1 = self._get_decimals(token1)
            price_of_token0 = ((slot0[0] / 2 ** 96) ** 2) / \
                              (10 ** decimals_token1 / 10 ** decimals_token0)
            if Web3.to_checksum_address(token0) == self.src_token and Web3.to_checksum_address(
                    token1) == self.dest_token:
                return price_of_token0
            else:
                return 1 / price_of_token0
        except Exception as e:
            logging.error(f"Error in _get_v3_price: {e}")

    def _get_aggregator_price(self) -> float:
        w3 = self._connect_web3()
        try:
            aggregator_contract = w3.eth.contract(
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
            logging.error(f"Error in _get_aggregator_price: {e}")

    def get_price(self):
        if self.name.split("_")[1] == "aggregator":
            price = self._get_aggregator_price()
            src_token_symbol, dest_token_symbol = self._get_tokens_symbol()
            logging.info(
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
                logging.info(f"Price of {dest_token_symbol} {1 / price}")
                logging.info(f"Price of {src_token_symbol}  {price}")
            else:
                logging.info("Pool doesn't exist.")
