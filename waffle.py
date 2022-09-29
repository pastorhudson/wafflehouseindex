import asyncio
import csv
import json

import aioredis
from bs4 import BeautifulSoup
from pydantic import BaseSettings
from tqdm import tqdm
import httpx
from datetime import datetime


async def get_stores():
    cookies = {
        'lg_session_v1': 'eyJpdiI6IktSeWNVUzBRcDNkT1kwM0NmemxjT216TW1FV1M3YTRaTkZtaytLWUg1R0U9IiwidmFsdWUiOiJQUzVZbmpvWjcyRkJHY29JSDh0Tjl3M1BDY0RKa1wvNnQxUjFxVlZackU1R3BaVngyUzBHb0pGdW1lVHB1QnR2TXFvY3g1SnlFQWZCMm94eFNOMm1xbVE9PSIsIm1hYyI6ImFiOWE1ODQwNmZkNmZlMmM4OGVjNWMwOWEyY2Y0NWIyNTI2N2ExNzZiZTg2YTJhNDJiYWM0NjAxNWU5NjE1ZTQifQ%3D%3D',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'https://wafflehouse.locally.com/conversion?company_id=117995&inline=1&lang=en-us&is_llp_sl=true&host_domain=locations.wafflehouse.com',
        # 'Cookie': 'lg_session_v1=eyJpdiI6IktSeWNVUzBRcDNkT1kwM0NmemxjT216TW1FV1M3YTRaTkZtaytLWUg1R0U9IiwidmFsdWUiOiJQUzVZbmpvWjcyRkJHY29JSDh0Tjl3M1BDY0RKa1wvNnQxUjFxVlZackU1R3BaVngyUzBHb0pGdW1lVHB1QnR2TXFvY3g1SnlFQWZCMm94eFNOMm1xbVE9PSIsIm1hYyI6ImFiOWE1ODQwNmZkNmZlMmM4OGVjNWMwOWEyY2Y0NWIyNTI2N2ExNzZiZTg2YTJhNDJiYWM0NjAxNWU5NjE1ZTQifQ%3D%3D',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }

    params = {
        'has_data': 'true',
        'company_id': '117995',
        'store_mode': '',
        'style': '',
        'color': '',
        'upc': '',
        'category': '',
        'inline': '1',
        'show_links_in_list': '',
        'parent_domain': '',
        'map_center_lat': '29.569773019147625',
        'map_center_lng': '-83.53968697813477',
        'map_distance_diag': '3000',
        'sort_by': 'proximity',
        'no_variants': '0',
        'only_retailer_id': '',
        'dealers_company_id': '',
        'only_store_id': 'false',
        'uses_alt_coords': 'false',
        'q': 'false',
        'zoom_level': '4',
        'lang': 'en-us',
    }
    async with httpx.AsyncClient() as client:
        response = await client.get('https://wafflehouse.locally.com/stores/conversion_data', params=params,
                                    cookies=cookies,
                                    headers=headers)

    return response.json()


async def format_data(locations_json: dict, redis) -> list:
    stores = []
    for store in tqdm(locations_json['markers']):
        try:
            _cache = json.loads(await redis.get('_stores' or ""))
            _cache.append({'Store ID': store['id'],
                           'Name': store['name'],
                           'State': store['state'],
                           'City': store['city'],
                           'Address': store['address'],
                           'Zip': store['zip'],
                           'Phone': store['phone'],
                           'Status': await get_single_store_status(store['id'])})
        except TypeError:
            _cache = [{'Store ID': store['id'],
                       'Name': store['name'],
                       'State': store['state'],
                       'City': store['city'],
                       'Address': store['address'],
                       'Zip': store['zip'],
                       'Phone': store['phone'],
                       'Status': await get_single_store_status(store['id'])}]
        await redis.set('_stores', json.dumps(_cache))

        # stores.append({'Store ID': store['id'],
        #                'Name': store['name'],
        #                'State': store['state'],
        #                'City': store['city'],
        #                'Address': store['address'],
        #                'Zip': store['zip'],
        #                'Phone': store['phone'],
        #                'Status': await get_single_store_status(store['id'])})

    return json.loads(await redis.get('_stores'))


async def write_stores(redis):
    stores_json = await get_stores()
    stores = await format_data(stores_json, redis)
    closed_stores = {'stores': stores, 'last_updated': datetime.utcnow()}
    await redis.set('stores_status', json.dumps(closed_stores))
    # with open('stores.csv', 'w', newline='') as csvfile:
    #     fieldnames = ['Store ID', 'Name', 'State', 'City', 'Address', 'Zip', 'Phone', 'Status']
    #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #
    #     writer.writeheader()
    #     for row in tqdm(stores):
    #         writer.writerow(row)
    # print(f'Store: {row["Store ID"]} - {row["Status"]}')


async def get_single_store_status(store_id: str) -> str:
    async with httpx.AsyncClient() as client:
        status_response = await client.get(f"https://wafflehouse.locally.com/conversion/location/store/{store_id}")
        # status_response = requests.get(f"https://wafflehouse.locally.com/conversion/location/store/{store_id}")
        if "Closed".lower() in status_response.json()['store_html'].lower():
            store_html = BeautifulSoup(status_response.json()['store_html'], features="html.parser")
            status = f"{store_html.find('span', attrs={'class': 'store-status'}).text} - {store_html.find('span', attrs={'class': 'store-info-subtitle'}).text}"
            return status
        else:
            return 'Open'


async def get_closed_stores_by_state(redis):
    closed_stores = []
    try:
        for store in json.loads(await redis.get('stores_status')):
            if "closed".lower() in store['Status'].lower():
                # closed_by_state[store['state']] += [store]
                closed_stores.append(store)
    except TypeError:
        closed_stores = {"Still Caching": True}
    return closed_stores

if __name__ == "__main__":
    class Config(BaseSettings):
        # The default URL expects the app to run using Docker and docker-compose.
        redis_url: str = 'redis://127.0.0.1:6379'

    config = Config()
    redis = aioredis.from_url(config.redis_url, decode_responses=True)
    asyncio.run(write_stores(redis))
