import os
import tweepy
import asyncio
import re
import json
import logging
import aiohttp
from find_spread.find_spread import find_spread

TRACK_KEYWORDS = ["new listing", "now listed", "token launch", "new token", "available now", "listing", "listed"]
TOKEN_REGEX = r'\b[A-Z]{2,6}\b'

logging.basicConfig(level=logging.INFO, filename='missing_tokens.log', filemode='a', format='%(asctime)s - %(message)s')

proxy_url = os.getenv("PROXY_URL")
os.environ["HTTP_PROXY"] = os.getenv("PROXY_URL")
os.environ["HTTPS_PROXY"] = os.getenv("PROXY_URL")

os.environ["ALL_PROXY"] = os.getenv("SOCKS_PROXY_URL")

with open('../tokens_coins_info/coins_info.json') as f:
    token_data = json.load(f)


async def fetch_token_data(token):
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={token.lower()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy_url) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    coin_info = {
                        "name": data[0]['symbol'].upper(),
                        "coin_id": data[0]['id'],
                        "blockchains": {
                            "Ethereum": data[0].get("platforms", {}).get("ethereum", ""),
                            "Binance Smart Chain": data[0].get("platforms", {}).get("binance-smart-chain", "")
                        }
                    }
                    return coin_info
            else:
                logging.info(f"Token '{token}' not found on CoinGecko.")
    return None


async def update_coins_info(new_token_info):
    token_data.append(new_token_info)
    with open('coins_info.json', 'w') as f:
        json.dump(token_data, f, indent=4)
    logging.info(f"Added new token info: {new_token_info['name']}")


class MyStreamListener(tweepy.StreamingClient):
    async def on_tweet(self, tweet):
        text = tweet.text
        tokens = re.findall(TOKEN_REGEX, text)

        found_tokens = []
        missing_tokens = []

        for token in tokens:
            matched_token_data = next((item for item in token_data if item["name"] == token), None)
            if matched_token_data:
                found_tokens.append(matched_token_data)
            else:
                token_info = await fetch_token_data(token)
                if token_info:
                    found_tokens.append(token_info)
                    await update_coins_info(token_info)
                else:
                    missing_tokens.append(token)
                    logging.info(f"Token '{token}' not found and could not be fetched from API.")

        if found_tokens:
            await self.check_spread_for_tokens(found_tokens)

    async def check_spread_for_tokens(self, tokens):
        tasks = [find_spread([token]) for token in tokens]
        await asyncio.gather(*tasks)


client = MyStreamListener(os.getenv("X_BEARER_TOKEN"))


async def main():
    await client.add_rules(tweepy.StreamRule(" OR ".join(TRACK_KEYWORDS)))
    await client.filter(tweet_fields=["text"])


asyncio.run(main())
