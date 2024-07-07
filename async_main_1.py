import asyncio
import aiohttp
import ujson as json
import pandas as pd
import logging

from web3 import Web3
from cexs.cex_exchanges import Bybit_exchange, Binance_exchange, Bingx_exchange, Bitfinex_exchange, Bitget_exchange, Bitmex_exchange, Bitstamp_exchange, Coinbase_exchange, Coinw_exchange, Cryptocom_exchange, Deribit_exchange, Dydx_exchange, Garantex_exchange, Gateio_exchange, Gemini_exchange, Huobi_exchange, Kraken_exchange, Kucoin_exchange, Mexc_exchange, Okx_exchange, Phemex_exchange, Poloniex_exchange, Youbit_exchange, Zigzag_exchange, Coinex_exchange, Backpack_exchange
from cexs.async_get_cex_price import BybitPrice, BingxPrice, BitfinexGeminiPrice, BitgetCoinwKucoinPrice, BitmexPrice, CexPrice, CryptocomPrice, DeribitPrice, DydxPrice, GarantexPrice, HuobiPrice, KrakenPrice, OkxPrice, PhemexPrice, PoloniexPrice, YoubitPrice, CoinexPrice, BackpackPrice
from dexs.async_get_dex_price import DexscreenerAggregatorApi, ParaswapAggregatorApi, KyberswapAggregatorApi, OpenoceanAggregatorApi, OneInchAggregatorApi
from dexs.networks import Ethereum, BinanceSmartChain, Arbitrum, Optimism, Polygon, Avalanche

logging.basicConfig(level=logging.INFO)


def find_spread(exchanges, aggregators):
    min_ask_exchange = min_ask_value = min_ask_pair = asks_volumes = None
    max_bid_exchange = max_bid_value = max_bid_pair = bids_volumes = None
    aggregator_sell = network_sell = price_sell = dex_sell = data_sell = None
    aggregator_buy = network_buy = price_buy = dex_buy = data_buy = None

    min_asks_exist = 'min_asks_price' in exchanges[0]['data'] if exchanges else False
    max_bids_exist = 'max_bids_price' in exchanges[0]['data'] if exchanges else False
    dex_price_sell_exist = 'price_sell' in aggregators[0] if aggregators else False
    dex_price_buy_exist = 'price_buy' in aggregators[0] if aggregators else False

    if min_asks_exist:
        df_cex = pd.DataFrame([
            {
                'exchange': d['exchange'],
                'pair': d['data'].get('pair', ''),
                'min_asks_price': d['data'].get('min_asks_price', ''),
                'asks_volumes': d['data'].get('asks_volumes', '')
            } for d in exchanges if d.get('data')
        ])
        if not df_cex.empty:
            min_ask_row = df_cex.dropna(
                subset=['min_asks_price']).loc[df_cex['min_asks_price'].idxmin()]
            min_ask_exchange, min_ask_value, min_ask_pair, asks_volumes = (
                min_ask_row['exchange'], min_ask_row['min_asks_price'],
                min_ask_row['pair'], min_ask_row['asks_volumes']
            )

    if max_bids_exist:
        df_cex = pd.DataFrame([
            {
                'exchange': d['exchange'],
                'pair': d['data'].get('pair', ''),
                'max_bids_price': d['data'].get('max_bids_price', ''),
                'bids_volumes': d['data'].get('bids_volumes', '')
            } for d in exchanges if d.get('data')
        ])
        if not df_cex.empty:
            max_bid_row = df_cex.dropna(
                subset=['max_bids_price']).loc[df_cex['max_bids_price'].idxmax()]
            max_bid_exchange, max_bid_value, max_bid_pair, bids_volumes = (
                max_bid_row['exchange'], max_bid_row['max_bids_price'],
                max_bid_row['pair'], max_bid_row['bids_volumes']
            )

    if dex_price_sell_exist:
        df_dex_sell = pd.DataFrame([
            {
                'aggregator_sell': d.get('aggregator_sell', ''),
                'network_sell': d.get('network_sell', ''),
                'price_sell': d.get('price_sell', ''),
                'dex_sell': d.get('dex_sell', ''),
                'data_sell': d.get('data_sell', ''),
                'src_sell_address': d.get('src_sell_address', ''),
                'dest_sell_address': d.get('dest_sell_address', '')
            } for d in aggregators if d.get('price_sell')
        ])

        if not df_dex_sell.empty:
            max_dex_sell_price = df_dex_sell.dropna(
                subset=['price_sell']).loc[df_dex_sell['price_sell'].idxmax()]
            aggregator_sell, network_sell, price_sell, dex_sell, data_sell, src_sell_address, dest_sell_address = (
                max_dex_sell_price['aggregator_sell'],
                max_dex_sell_price['network_sell'],
                max_dex_sell_price['price_sell'],
                max_dex_sell_price['dex_sell'],
                max_dex_sell_price['data_sell'],
                max_dex_sell_price['src_sell_address'],
                max_dex_sell_price['dest_sell_address'],
            )

    if dex_price_buy_exist:
        df_dex_buy = pd.DataFrame([
            {
                'aggregator_buy': d.get('aggregator_buy', ''),
                'network_buy': d.get('network_buy', ''),
                'price_buy': d.get('price_buy', ''),
                'dex_buy': d.get('dex_buy', ''),
                'data_buy': d.get('data_buy', ''),
                'src_buy_address': d.get('src_buy_address', ''),
                'dest_buy_address': d.get('dest_buy_address', '')
            } for d in aggregators if d.get('price_buy')
        ])

        if not df_dex_buy.empty:
            min_dex_buy_price = df_dex_buy.dropna(
                subset=['price_buy']).loc[df_dex_buy['price_buy'].idxmin()]
            aggregator_buy, network_buy, price_buy, dex_buy, data_buy, src_buy_address, dest_buy_address = (
                min_dex_buy_price['aggregator_buy'],
                min_dex_buy_price['network_buy'],
                min_dex_buy_price['price_buy'],
                min_dex_buy_price['dex_buy'],
                min_dex_buy_price['data_buy'],
                min_dex_buy_price['src_buy_address'],
                min_dex_buy_price['dest_buy_address']
            )

    if min_asks_exist and max_bids_exist and dex_price_sell_exist and dex_price_buy_exist:
        if price_sell > max_bid_value and price_buy < min_ask_value:
            percents_spread = (float(price_sell) /
                               float(price_buy) * 100) - 100

            result_dex_output = (
                f"Aggregator with minimum price: {aggregator_buy}\n"
                f"Aggregator min price: {price_buy}\n"
                f"Network buy: {network_buy}, dex buy: {dex_buy}\n"
                f"Data buy: {data_buy}\n\n"
                f"Aggregator with maximum price: {aggregator_sell}\n"
                f"Aggregator max price: {price_sell}\n"
                f"Network sell: {network_sell}, dex sell: {dex_sell}\n"
                f"Data sell: {data_sell}\n"
                f"Spread: {percents_spread}%\n"
                f"Exchange with maximum 'max_bids_price': {max_bid_exchange}, "
                f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
                f"-------------------------------------------------\n\n"
            )
            print(result_dex_output)

            if network_buy == "Ethereum" or network_sell == "Ethereum":
                if percents_spread >= 15:
                    signal_output = (
                        f"Aggregator with minimum price: {aggregator_buy}\n"
                        f"Aggregator min price: {price_buy}\n"
                        f"Network buy: {network_buy}, dex buy: {dex_buy}\n"
                        f"Data buy: {data_buy}\n\n"
                        f"Aggregator with maximum price: {aggregator_sell}\n"
                        f"Aggregator max price: {price_sell}\n"
                        f"Network sell: {network_sell}, dex sell: {dex_sell}\n"
                        f"Data sell: {data_sell}\n\n"
                        f"Spread: {percents_spread}%\n\n"
                        f"All data: {aggregators}\n\n"
                        f"Buy token address {src_buy_address}, sell token address {src_sell_address}\n\n"
                        f"Exchange with maximum 'max_bids_price': {max_bid_exchange}, "
                        f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
                        f"-------------------------------------------------\n\n"
                    )
                    print(f"**********SIGNAL**********")
                    print(signal_output)
                    with open('results/async_signals_1.txt', 'a') as file:
                        file.write(signal_output)
            else:
                if percents_spread >= 3:
                    signal_output = (
                        f"Aggregator with minimum price: {aggregator_buy}\n"
                        f"Aggregator min price: {price_buy}\n"
                        f"Network buy: {network_buy}, dex buy: {dex_buy}\n"
                        f"Data buy: {data_buy}\n\n"
                        f"Aggregator with maximum price: {aggregator_sell}\n"
                        f"Aggregator max price: {price_sell}\n"
                        f"Network sell: {network_sell}, dex sell: {dex_sell}\n"
                        f"Data sell: {data_sell}\n\n"
                        f"Spread: {percents_spread}%\n"
                        f"All data: {aggregators}\n\n"
                        f"Buy token address {src_buy_address}, sell token address {src_sell_address}\n\n"
                        f"Exchange with maximum 'max_bids_price': {max_bid_exchange}, "
                        f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
                        f"-------------------------------------------------\n\n"
                    )
                    print(f"**********SIGNAL**********")
                    print(signal_output)
                    with open('results/async_signals_1.txt', 'a') as file:
                        file.write(signal_output)

            with open('results/async_results_1.txt', 'a') as file:
                file.write(result_dex_output)

        if price_sell > max_bid_value and price_buy > min_ask_value and min_ask_value != 0:
            percents_spread = (float(price_sell) /
                               float(min_ask_value) * 100) - 100
            asks_amount = float(min_ask_value) * float(asks_volumes)

            result_dex_output = (
                f"Exchange with minimum price: {min_ask_exchange}, "
                f"Price: {min_ask_value}, Pair: {min_ask_pair}\n\n"
                f"Aggregator with maximum price: {aggregator_sell}\n"
                f"Aggregator price: {price_sell}\n"
                f"Ask amount: {asks_amount}\n"
                f"Network: {network_sell}, dex: {dex_sell}\n"
                f"Data: {data_sell}\n"
                f"Spread: {percents_spread}%\n"
                f"-------------------------------------------------\n\n"
            )
            print(result_dex_output)

            if network_sell == "Ethereum":
                if percents_spread >= 10 and asks_amount >= 100:
                    signal_output = (
                        f"Exchange with minimum price: {min_ask_exchange}, "
                        f"Price: {min_ask_value}, Pair: {min_ask_pair}\n\n"
                        f"Aggregator with maximum price: {aggregator_sell}\n"
                        f"Aggregator price: {price_sell}\n"
                        f"Ask amount: {asks_amount}\n"
                        f"Network: {network_sell}, dex: {dex_sell}\n"
                        f"Data: {data_buy}\n\n"
                        f"Spread: {percents_spread}%\n\n"
                        f"All data: {aggregators}\n\n"
                        f"Exchange with maximum 'max_bids_price': {max_bid_exchange}, "
                        f"Price: {max_bid_value}, Pair: {max_bid_pair}\n\n"
                        f"Buy token address {src_buy_address}, sell token address {src_sell_address}\n\n"
                        f"-------------------------------------------------\n\n"
                    )
                    print(f"**********SIGNAL**********")
                    print(signal_output)
                    with open('results/async_signals_1.txt', 'a') as file:
                        file.write(signal_output)
            else:
                if percents_spread >= 3 and asks_amount >= 50:
                    signal_output = (
                        f"Exchange with minimum price: {min_ask_exchange}, "
                        f"Price: {min_ask_value}, Pair: {min_ask_pair}\n\n"
                        f"Aggregator with maximum price: {aggregator_sell}\n"
                        f"Aggregator price: {price_sell}\n"
                        f"Ask amount: {asks_amount}\n"
                        f"Network: {network_sell}, dex: {dex_sell}\n"
                        f"Data: {data_sell}\n\n"
                        f"Spread: {percents_spread}%\n\n"
                        f"All data: {aggregators}%\n\n"
                        f"Exchange with maximum 'max_bids_price': {max_bid_exchange}, "
                        f"Price: {max_bid_value}, Pair: {max_bid_pair}\n\n"
                        f"Buy token address {src_buy_address}, sell token address {src_sell_address}\n\n"
                        f"-------------------------------------------------\n\n"
                    )
                    print(f"**********SIGNAL**********")
                    print(signal_output)
                    with open('results/async_signals_1.txt', 'a') as file:
                        file.write(signal_output)

            with open('results/async_results_1.txt', 'a') as file:
                file.write(result_dex_output)

        if price_sell < max_bid_value and price_buy < min_ask_value:
            percents_spread = (float(max_bid_value) /
                               float(price_buy) * 100) - 100
            asks_amount = float(max_bid_value) * float(bids_volumes)

            result_dex_output = (
                f"Aggregator with minimum price: {aggregator_buy}\n"
                f"Aggregator price: {price_buy}\n"
                f"Network: {network_buy}, dex: {dex_buy}\n"
                f"Data: {data_buy}\n\n"
                f"Exchange with maximum price: {max_bid_exchange}, "
                f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
                f"Ask amount: {asks_amount}\n\n"
                f"Spread: {percents_spread}%\n"
                f"-------------------------------------------------\n\n"
            )
            print(result_dex_output)

            if network_buy == "Ethereum":
                if percents_spread >= 10 and asks_amount >= 100:
                    signal_output = (
                        f"Aggregator with minimum price: {aggregator_buy}\n"
                        f"Aggregator price: {price_buy}\n"
                        f"Network: {network_buy}, dex: {dex_buy}\n"
                        f"Data: {data_buy}\n\n"
                        f"Exchange with maximum price: {max_bid_exchange}, "
                        f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
                        f"Ask amount: {asks_amount}\n"
                        f"Spread: {percents_spread}%\n"
                        f"All data: {aggregators}\n\n"
                        f"Exchange with minimum price: {min_ask_exchange}, "
                        f"Price: {min_ask_value}, Pair: {min_ask_pair}\n\n"
                        f"Buy token address {src_buy_address}, sell token address {src_sell_address}\n\n"
                        f"-------------------------------------------------\n\n"
                    )
                    print(f"**********SIGNAL**********")
                    print(signal_output)
                    with open('results/async_signals_1.txt', 'a') as file:
                        file.write(signal_output)

            else:
                if percents_spread >= 3 and asks_amount >= 50:
                    signal_output = (
                        f"Aggregator with minimum price: {aggregator_buy}\n"
                        f"Aggregator price: {price_buy}\n"
                        f"Network: {network_buy}, dex: {dex_buy}\n"
                        f"Data: {data_buy}\n\n"
                        f"Exchange with maximum price: {max_bid_exchange}, "
                        f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
                        f"Ask amount: {asks_amount}\n\n"
                        f"Spread: {percents_spread}%\n"
                        f"All data: {aggregators}\n\n"
                        f"Exchange with minimum price: {min_ask_exchange}, "
                        f"Price: {min_ask_value}, Pair: {min_ask_pair}\n\n"
                        f"Buy token address {src_buy_address}, sell token address {src_sell_address}\n\n"
                        f"-------------------------------------------------\n\n"
                    )
                    print(f"**********SIGNAL**********")
                    print(signal_output)
                    with open('results/async_signals_1.txt', 'a') as file:
                        file.write(signal_output)

            with open('results/async_results_1.txt', 'a') as file:
                file.write(result_dex_output)

    if min_asks_exist and max_bids_exist:
        percents_spread = (float(max_bid_value) /
                           float(min_ask_value) * 100) - 100
        asks_amount = float(min_ask_value) * float(asks_volumes)
        bids_amount = float(max_bid_value) * float(bids_volumes)

        result_output = (
            f"Exchange with minimum 'min_asks_price': {min_ask_exchange}, "
            f"Price: {min_ask_value}, Pair: {min_ask_pair}\n"
            f"Asks amount: {asks_amount}\n\n"
            f"Exchange with maximum 'max_bids_price': {max_bid_exchange}, "
            f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
            f"Bids amount: {bids_amount}\n\n"
            f"Difference: {percents_spread}%\n"
            f"-------------------------------------------------\n\n"
        )
        print(result_output)

        if percents_spread >= 3 and asks_amount >= 50 and bids_amount >= 50:
            print(f"**********SIGNAL**********")
            print(result_output)
            with open('results/async_signals_1.txt', 'a') as file:
                file.write(result_output)

        with open('results/async_results_1.txt', 'a') as file:
            file.write(result_output)


async def cex_prices(src_token, dest_token):
    cexs = {Bybit_exchange: BybitPrice,
            Binance_exchange: CexPrice,
            Bingx_exchange: BingxPrice,
            Bitfinex_exchange: BitfinexGeminiPrice,
            Bitget_exchange: BitgetCoinwKucoinPrice,
            Bitmex_exchange: BitmexPrice,
            Bitstamp_exchange: CexPrice,
            # Bittrex_exchange,
            Coinbase_exchange: CexPrice,
            Coinw_exchange: BitgetCoinwKucoinPrice,
            Cryptocom_exchange: CryptocomPrice,
            Deribit_exchange: DeribitPrice,
            Dydx_exchange: DydxPrice,
            Garantex_exchange: GarantexPrice,
            Gateio_exchange: CexPrice,
            Gemini_exchange: BitfinexGeminiPrice,
            Huobi_exchange: HuobiPrice,
            # Kine_exchange,
            # THERE IS NO MAX AND MIN PRICES
            Kraken_exchange: KrakenPrice,
            Kucoin_exchange: BitgetCoinwKucoinPrice,
            Mexc_exchange: CexPrice,
            Okx_exchange: OkxPrice,
            Phemex_exchange: PhemexPrice,
            Poloniex_exchange: PoloniexPrice,
            Youbit_exchange: YoubitPrice,
            # Zigzag_exchange: CexPrice,
            Coinex_exchange: CoinexPrice,
            Backpack_exchange: BackpackPrice
            }

    cexs_price_list = []
    cex_price_info = {}
    if src_token not in ["USDT", "USDC"]:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for cex, obj in cexs.items():
                cex.src_token = src_token["name"]
                cex.dest_token = dest_token
                exchange = obj(exchange=cex)
                tasks.append(exchange.get_price(session=session))

            results = await asyncio.gather(*tasks)
            for result in results:
                logging.info(f"result {result}")
                if result:
                    cex_price_info = {
                        "exchange": result["exchange"], "data": result}
                    cexs_price_list.append(cex_price_info)
                    logging.info(
                        f"\nEXIT Print from cex_prices\ncex_price_info: {cex_price_info}\n")

    return cexs_price_list


async def dex_prices(src_token, dest_token):
    aggregators = [ParaswapAggregatorApi,
                   KyberswapAggregatorApi,
                   OpenoceanAggregatorApi,
                   OneInchAggregatorApi,
                   DexscreenerAggregatorApi]
    networks = [Ethereum,
                BinanceSmartChain,
                Arbitrum,
                Optimism,
                Polygon,
                Avalanche]
    if dest_token == "USDT":
        dest_token = json.load(open("tokens_coins_info/usdt_adresses.json"))
    elif dest_token == "USDC":
        dest_token = json.load(open("tokens_coins_info/usdc_adresses.json"))
    else:
        print(f"Not USDT or USDC")
    aggregator_price_info = {}
    aggregator_price_list = []
    async with aiohttp.ClientSession() as session:
        tasks_dex_sell = []
        tasks_dex_buy = []
        for aggregator in aggregators:
            for network in networks:
                if src_token not in ["USDT", "USDC"]:
                    if network.name in src_token["blockchains"]:
                        aggregator_object_sell = aggregator(
                            src_token=Web3.to_checksum_address(
                                src_token["blockchains"][network.name]),
                            dest_token=Web3.to_checksum_address(
                                dest_token[network.name]),
                            name="",
                            network=network
                        )
                        tasks_dex_sell.append(
                            aggregator_object_sell.get_price(session=session))

                        aggregator_object_buy = aggregator(
                            src_token=Web3.to_checksum_address(
                                dest_token[network.name]),
                            dest_token=Web3.to_checksum_address(
                                src_token["blockchains"][network.name]),
                            name="",
                            network=network
                        )
                        tasks_dex_buy.append(
                            aggregator_object_buy.get_price(session=session))

        results_dex_sell = await asyncio.gather(*tasks_dex_sell)
        results_dex_buy = await asyncio.gather(*tasks_dex_buy)

        for result_dex_sell in results_dex_sell:
            if result_dex_sell:
                if result_dex_sell["price"] != 0 and result_dex_sell["price"] != None:
                    if "data" in result_dex_sell:
                        aggregator_price_info.update({"aggregator_sell": result_dex_sell["aggregator"],
                                                "network_sell": result_dex_sell["network"],
                                                "src_sell_address": result_dex_sell["src_address"],
                                                "dest_sell_address": result_dex_sell["dest_address"],
                                                "price_sell": float(result_dex_sell["price"]),
                                                "dex_sell": result_dex_sell["dex"],
                                                "data_sell": result_dex_sell["data"]})
                    else:
                        aggregator_price_info.update({"aggregator_sell": result_dex_sell["aggregator"],
                                                "network_sell": result_dex_sell["network"],
                                                "src_sell_address": result_dex_sell["src_address"],
                                                "dest_sell_address": result_dex_sell["dest_address"],
                                                "price_sell": float(result_dex_sell["price"]),
                                                "dex_sell": result_dex_sell["dex"],
                                                "data_sell": ""})
        for result_dex_buy in results_dex_buy:
            if result_dex_buy:
                if result_dex_buy["price"] != 0 and result_dex_buy["price"] != None:
                    if "data" in result_dex_buy:
                        aggregator_price_info.update({"aggregator_buy": result_dex_buy["aggregator"],
                                                      "network_buy": result_dex_buy["network"],
                                                      "src_buy_address": result_dex_buy["src_address"],
                                                      "dest_buy_address": result_dex_buy["dest_address"],
                                                      "price_buy": 1 / float(result_dex_buy["price"]),
                                                      "dex_buy": result_dex_buy["dex"],
                                                      "data_buy": result_dex_buy["data"]})
                    else:
                        aggregator_price_info.update({"aggregator_buy": result_dex_buy["aggregator"],
                                                      "network_buy": result_dex_buy["network"],
                                                      "src_buy_address": result_dex_buy["src_address"],
                                                      "dest_buy_address": result_dex_buy["dest_address"],
                                                      "price_buy": 1 / float(result_dex_buy["price"]),
                                                      "dex_buy": result_dex_buy["dex"],
                                                      "data_buy": ""})
        logging.info(
            f"\nEXIT Print from dex_prices\ndex_price_info: {aggregator_price_info}\n")
        aggregator_price_list.append(aggregator_price_info)
        logging.info(f"EXIT PRICE LIST:\n{aggregator_price_list}\n")
    return aggregator_price_list


async def main():
    coins_info = json.load(open("tokens_coins_info/coins_info_1.json"))
    for src_token in coins_info:
        print("***************************")
        print(f"USDT - {src_token}")
        exchanges = await cex_prices(src_token, dest_token="USDT")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!CEX{exchanges}")
        aggregators = await dex_prices(src_token, dest_token="USDT")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!DEX{aggregators}")
        find_spread(exchanges, aggregators)
        print("***************************")
        print(f"USDC - {src_token}")
        exchanges = await cex_prices(src_token, dest_token="USDC")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!CEX{exchanges}")
        aggregators = await dex_prices(src_token, dest_token="USDC")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!DEX{aggregators}")
        find_spread(exchanges, aggregators)

if __name__ == "__main__":
    asyncio.run(main())
