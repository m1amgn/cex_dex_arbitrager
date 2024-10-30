import asyncio
import ujson as json
from find_spread import find_spread


def split_tokens(tokens, num_parts):
    avg_len = len(tokens) // num_parts
    return [tokens[i * avg_len:(i + 1) * avg_len] for i in range(num_parts - 1)] + [tokens[(num_parts - 1) * avg_len:]]


async def main():
    with open("tokens_coins_info/coins_info.json", "r") as file:
        coins_info = json.load(file)

    token_groups = split_tokens(coins_info, 3)

    tasks = []
    for idx, tokens in enumerate(token_groups, start=1):
        tasks.append(find_spread(tokens))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
