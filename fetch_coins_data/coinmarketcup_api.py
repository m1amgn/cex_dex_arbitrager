import requests
import ujson as json
import time
import os

from dotenv import load_dotenv

load_dotenv()


def get_blockchain_info():
    api_key = os.getenv('COINMARKETCUP_API_KEY')
    coins_info = json.load(open("coins_info_coinmarketcup.json"))
    try:
        for coins in coins_info:
            if not coins["blockchains"]:
                print(coins)
                url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?id={str(coins['coin_id'])}"

                headers = {
                    'Accepts': 'application/json',
                    'X-CMC_PRO_API_KEY': api_key,
                }

                response = requests.get(url, headers=headers)
                data = response.json()

                if response.status_code == 200:
                    for blockchain in data['data'][str(coins['coin_id'])]['contract_address']:
                        coins["blockchains"].update({blockchain["platform"]["name"]: blockchain["contract_address"]})
                        coins_info.append(coins["blockchains"])

                    with open("coins_info_coinmarketcup.json", "w") as file:
                        json.dump(coins_info, file, indent=4)

                elif response.status_code == 429:
                    time.sleep(60)
                    continue

                elif not coins:
                    return False

                else:
                    print(f"Error: {data['status']['error_message']}")
    except Exception as e:
        print(e)


def fetch_all_coins():
    api_key = os.getenv('COINMARKETCUP_API_KEY')
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    parameters = {
        'start': '1',
        'limit': '5000',
        'convert': 'USD'
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()
    print(data)

    if response.status_code == 200:
        coins_list = []
        coins_data = data['data']
        for coin in coins_data:
            symbol = coin['symbol']
            coin_id = coin['id']
            coins_list.append(
                {"name": symbol, "coin_id": coin_id, "blockchains": {}})
        with open("coins_info_coinmarketcup.json", "w") as file:
            json.dump(coins_list, file, indent=4)

    else:
        print(f"Error: {data['status']['error_message']}")


def test_get_blockchain_info(api_key):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?id=5426"

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    response = requests.get(url, headers=headers)
    print(response.text)


def get_all_chains():
    coins_info = json.load(open("coins_info.json"))

    chains_list = []

    for coins in coins_info:
        if coins["blockchains"]:
            for keys in coins["blockchains"].keys():
                if keys not in chains_list:
                    chains_list.append(keys)

    print(chains_list)


while True:
    get_blockchain_info()
    # fetch_all_coins()
    # test_get_blockchain_info()
    # get_all_chains()
