import asyncio
import ujson as json
from async_main import cex_prices, dex_prices, find_spread

SRC_TOKEN = "XAI"
DEST_TOKEN = "USDT"


def get_token_from_list(token: str) -> dict:
    coins_info = json.load(open("tokens_coins_info/coins_info.json"))
    for coins in coins_info:
        if coins['name'] == token:
            return coins
        else:
            print(f"No {token} in the list.")


async def main(src_token: str, dest_token: str) -> None:
    src_token = get_token_from_list(src_token)
    exchanges = await cex_prices(src_token, dest_token)
    aggregators = await dex_prices(src_token, dest_token)
    find_spread(exchanges, aggregators)

if __name__ == "__main__":
    asyncio.run(main(SRC_TOKEN, DEST_TOKEN))
