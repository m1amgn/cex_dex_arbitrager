import asyncio
import ujson as json
from find_spread import calculate_spread, cex_prices, dex_prices

SRC_TOKEN = "TENET"
DEST_TOKEN = "USDT"
PART_OF_FILES = "by_pairs"


def get_token_from_list(token: str) -> dict:
    coins_info = json.load(open("tokens_coins_info/coins_info.json"))
    for coins in coins_info:
        if coins['name'] == token:
            return coins
        else:
            print(f"No {token} in the list.")


async def main(src_token: str, dest_token: str, part_of_files) -> None:
    src_token = get_token_from_list(src_token)
    exchanges = await cex_prices(src_token, dest_token)
    aggregators = await dex_prices(src_token, dest_token)
    print(f"\n\n\nCEXES - {exchanges}\n\n\nDEXES - {aggregators}\n\n\n")
    calculate_spread(exchanges, aggregators, part_of_files)

if __name__ == "__main__":
    asyncio.run(main(SRC_TOKEN, DEST_TOKEN, PART_OF_FILES))
