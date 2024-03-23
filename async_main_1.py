import asyncio
import aiohttp
import json
import pandas as pd

from cexs.cex_exchanges import Bybit_exchange, Binance_exchange, Bingx_exchange, Bitfinex_exchange, Bitget_exchange, Bitmex_exchange, Bitstamp_exchange, Coinbase_exchange, Coinw_exchange, Cryptocom_exchange, Deribit_exchange, Dydx_exchange, Garantex_exchange, Gateio_exchange, Gemini_exchange, Huobi_exchange, Kraken_exchange, Kucoin_exchange, Mexc_exchange, Okx_exchange, Phemex_exchange, Poloniex_exchange, Youbit_exchange, Zigzag_exchange
from cexs.async_get_cex_price import BybitPrice, BingxPrice, BitfinexGeminiPrice, BitgetCoinwKucoinPrice, BitmexPrice, CexPrice, CryptocomPrice, DeribitPrice, DydxPrice, GarantexPrice, HuobiPrice, KrakenPrice, OkxPrice, PhemexPrice, PoloniexPrice, YoubitPrice
from dexs.async_get_dex_price import DexscreenerAggregatorApi, ParaswapAggregatorApi, KyberswapAggregatorApi, OpenoceanAggregatorApi, OneInchAggregatorApi
from dexs.networks import Ethereum, BinanceSmartChain, Arbitrum, Optimism, Polygon, Avalanche


def find_spread(exchanges, aggregators):
    min_ask_exchange = min_ask_value = min_ask_pair = asks_volumes = None
    max_bid_exchange = max_bid_value = max_bid_pair = bids_volumes = None
    aggregator = network = dex_price = dex = data = None

    min_asks_exist = 'min_asks_price' in exchanges[0]['data'] if exchanges else False
    max_bids_exist = 'max_bids_price' in exchanges[0]['data'] if exchanges else False
    dex_price_exist = 'price' in aggregators[0] if aggregators else False

    if min_asks_exist:
        df_cex = pd.DataFrame([
            {
                'exchange': d['exchange'],
                'pair': d['data'].get('pair', 'N/A'),
                'min_asks_price': d['data'].get('min_asks_price', 'N/A'),
                'asks_volumes': d['data'].get('asks_volumes', 'N/A')
            } for d in exchanges if d.get('data')
        ])
        if not df_cex.empty:
            min_ask_row = df_cex.loc[df_cex['min_asks_price'].idxmin()]
            min_ask_exchange, min_ask_value, min_ask_pair, asks_volumes = (
                min_ask_row['exchange'], min_ask_row['min_asks_price'],
                min_ask_row['pair'], min_ask_row['asks_volumes']
            )

    if max_bids_exist:
        df_cex = pd.DataFrame([
            {
                'exchange': d['exchange'],
                'pair': d['data'].get('pair', 'N/A'),
                'max_bids_price': d['data'].get('max_bids_price', 'N/A'),
                'bids_volumes': d['data'].get('bids_volumes', 'N/A')
            } for d in exchanges if d.get('data')
        ])
        if not df_cex.empty:
            max_bid_row = df_cex.loc[df_cex['max_bids_price'].idxmax()]
            max_bid_exchange, max_bid_value, max_bid_pair, bids_volumes = (
                max_bid_row['exchange'], max_bid_row['max_bids_price'],
                max_bid_row['pair'], max_bid_row['bids_volumes']
            )

    if dex_price_exist:
        df_dex = pd.DataFrame([
            {
                'aggregator': d['aggregator'],
                'network': d['network'],
                'dex_price': d['price'],
                'dex': d['dex'],
                'data': d['data']
            } for d in aggregators
        ])

        if not df_dex.empty:
            max_dex_price = df_dex.loc[df_dex['dex_price'].idxmax()]
            aggregator, network, dex_price, dex, data = (
                max_dex_price['aggregator'], max_dex_price['network'],
                max_dex_price['dex_price'], max_dex_price['dex'], max_dex_price['data']
            )

    if min_asks_exist and max_bids_exist and dex_price_exist:
        percents_spread = (float(max_bid_value) /
                           float(min_ask_value) * 100) - 100
        asks_amount = float(min_ask_value) * float(asks_volumes)
        bids_amount = float(max_bid_value) * float(bids_volumes)

        result_cex_output = (
            f"Exchange with minimum 'min_asks_price': {min_ask_exchange}, "
            f"Price: {min_ask_value}, Pair: {min_ask_pair}\n"
            f"Asks amount: {asks_amount}\n"
            f"Exchange with maximum 'max_bids_price': {max_bid_exchange}, "
            f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
            f"Bibs amount: {bids_amount}\n"
            f"Difference: {percents_spread}%\n"
            f"-------------------------------------------------\n\n"
        )
        print(result_cex_output)

        if percents_spread >= 3 and asks_amount >= 50 and bids_amount >= 50:
            print(f"**********SIGNAL**********")
            print(result_cex_output)
            with open('results/async_signals_1.txt', 'a') as file:
                file.write(result_cex_output)

        if dex_price > max_bid_value:
            percents_spread = (float(dex_price) /
                               float(min_ask_value) * 100) - 100
            asks_amount = float(min_ask_value) * float(asks_volumes)

            result_dex_output = (
                f"Exchange with minimum 'min_asks_price': {min_ask_exchange}, "
                f"Price: {min_ask_value}, Pair: {min_ask_pair}\n"
                f"Aggregator with maximum price: {aggregator}\n"
                f"Aggregator price: {dex_price}\n"
                f"Ask amount: {asks_amount}\n"
                f"Network: {network}, dex: {dex}\n"
                f"Data: {data}\n"
                f"Difference: {percents_spread}%\n"
                f"-------------------------------------------------\n\n"
            )
            print(result_dex_output)

            if network == "Ethereum":
                if percents_spread >= 15 and asks_amount >= 100:
                    signal_output = (
                        f"Exchange with minimum 'min_asks_price': {min_ask_exchange}, "
                        f"Price: {min_ask_value}, Pair: {min_ask_pair}\n"
                        f"Aggregator with maximum price: {aggregator}\n"
                        f"Aggregator price: {dex_price}\n"
                        f"Ask amount: {asks_amount}\n"
                        f"Network: {network}, dex: {dex}\n"
                        f"Data: {data}\n"
                        f"Difference: {percents_spread}%\n\n"
                        f"All data: {aggregators}\n\n"
                        f"Exchange with maximum 'max_bids_price': {max_bid_exchange}, "
                        f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
                        f"-------------------------------------------------\n\n"
                    )
                    print(f"**********SIGNAL**********")
                    print(signal_output)
                    with open('results/async_signals_1.txt', 'a') as file:
                        file.write(signal_output)
            else:
                if percents_spread >= 3 and asks_amount >= 50:
                    signal_output = (
                        f"Exchange with minimum 'min_asks_price': {min_ask_exchange}, "
                        f"Price: {min_ask_value}, Pair: {min_ask_pair}\n"
                        f"Aggregator with maximum price: {aggregator}\n"
                        f"Aggregator price: {dex_price}\n"
                        f"Ask amount: {asks_amount}\n"
                        f"Network: {network}, dex: {dex}\n"
                        f"Data: {data}\n"
                        f"Difference: {percents_spread}%\n\n"
                        f"All data: {aggregators}%\n\n"
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

        with open('results/async_results_1.txt', 'a') as file:
            file.write(result_cex_output)

    if min_asks_exist and max_bids_exist and not dex_price_exist:
        percents_spread = (float(max_bid_value) /
                           float(min_ask_value) * 100) - 100
        asks_amount = float(min_ask_value) * float(asks_volumes)
        bids_amount = float(max_bid_value) * float(bids_volumes)

        result_output = (
            f"Exchange with minimum 'min_asks_price': {min_ask_exchange}, "
            f"Price: {min_ask_value}, Pair: {min_ask_pair}\n"
            f"Asks amount: {asks_amount}\n"
            f"Exchange with maximum 'max_bids_price': {max_bid_exchange}, "
            f"Price: {max_bid_value}, Pair: {max_bid_pair}\n"
            f"Bibs amount: {bids_amount}\n"
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
            Zigzag_exchange: CexPrice
            }
    cexs_price_list = []
    cex_price_info = {}
    if src_token not in ["USDT", "USDC"]:
        async with aiohttp.ClientSession() as session:
            for cex, obj in cexs.items():
                cex.src_token = src_token["name"]
                cex.dest_token = dest_token
                exchange = obj(exchange=cex)
                price_info = await exchange.get_price(session=session)
                if price_info:
                    cex_price_info = {"exchange": cex.name, "data": price_info}
                    cexs_price_list.append(cex_price_info)
                    print(
                        f"EXIT Print from cex_prices\nreponse.status\n{cex_price_info}")

    return cexs_price_list


async def dex_prices(src_token, dest_token):
    aggregators = [DexscreenerAggregatorApi, ParaswapAggregatorApi,
                   KyberswapAggregatorApi, OpenoceanAggregatorApi, OneInchAggregatorApi]
    networks = [Ethereum, BinanceSmartChain,
                Arbitrum, Optimism, Polygon, Avalanche]
    if dest_token == "USDT":
        dest_token = json.load(open("tokens_coins_info/usdt_adresses.json"))
    elif dest_token == "USDC":
        dest_token = json.load(open("tokens_coins_info/usdc_adresses.json"))
    else:
        print(f"Not USDT or USDC")
    aggregator_price_info = {}
    aggregator_price_list = []
    async with aiohttp.ClientSession() as session:
        for aggregator in aggregators:
            for network in networks:
                if src_token not in ["USDT", "USDC"]:
                    if network.name in src_token["blockchains"]:
                        aggregator_object = aggregator(
                            src_token=src_token["blockchains"][network.name],
                            dest_token=dest_token[network.name],
                            name="",
                            network=network
                        )
                        aggregator_data = await aggregator_object.get_price(session=session)
                        if aggregator_data:
                            if "data" in aggregator_data:
                                aggregator_price_info = {"aggregator": aggregator_object.name,
                                                         "network": network.name,
                                                         "price": float(aggregator_data["price"]),
                                                         "dex": aggregator_data["dex"],
                                                         "data": aggregator_data["data"]}
                            else:
                                aggregator_price_info = {"aggregator": aggregator_object.name,
                                                         "network": network.name,
                                                         "price": float(aggregator_data["price"]),
                                                         "dex": aggregator_data["dex"],
                                                         "data": ""}
                            print(
                                f"EXIT Print from dex_prices\nreponse.status\n{aggregator_price_info}")
                            aggregator_price_list.append(aggregator_price_info)
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
