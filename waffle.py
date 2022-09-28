import requests
from pprint import pprint
import csv
from bs4 import BeautifulSoup
from tqdm import tqdm


def get_stores():
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

    response = requests.get('https://wafflehouse.locally.com/stores/conversion_data', params=params, cookies=cookies, headers=headers)

    return response.json()


def format_data(locations_json: dict) -> list:

    stores = []
    for store in tqdm(locations_json['markers']):
        stores.append({'Store ID': store['id'],
                       'Name': store['name'],
                       'State': store['state'],
                       'City': store['city'],
                       'Address': store['address'],
                       'Zip': store['zip'],
                       'Phone': store['phone'],
                       'Status': store['is_temporarily_closed']})
    return stores


def write_stores():
    stores_json = get_stores()
    stores = format_data(stores_json)
    with open('stores.csv', 'w', newline='') as csvfile:
        fieldnames = ['Store ID', 'Name', 'State', 'City', 'Address', 'Zip', 'Phone', 'Status' ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in tqdm(stores):
            writer.writerow(row)
            # print(f'Store: {row["Store ID"]} - {row["Status"]}')


def get_single_store_status(store_id: str) -> str:
    status_response = requests.get(f"https://wafflehouse.locally.com/conversion/location/store/{store_id}")

    store_html = BeautifulSoup(status_response.json()['store_html'], features="html.parser")
    return store_html.find('span', attrs={'class': 'store-status'}).text


# def update_status():
#     updated_stores = []
#
#     with open('updated_stores.csv', 'w', newline='') as csvfile:
#         fieldnames = ['Store ID', 'State', 'City', 'Address', 'Zip', 'Phone', 'Status' ]
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#
#         writer.writeheader()
#         for row in get_stores():
#             writer.writerow(row)


if __name__ == "__main__":
    print(write_stores())
