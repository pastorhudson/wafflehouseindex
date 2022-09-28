from pprint import pprint

import requests

cookies = {
    'lg_session_v1': 'eyJpdiI6Inp2Qlk0TTQxVXhRZU5OZXJWUlpFRzZMQng1d0t5NGpwQkdFbEJCVkY0Q009IiwidmFsdWUiOiJcL2RMK291eWRsQ2VKTGlYT2paSTVzXC9ydW9jV3ZLQ1wvYXZvenRcL0U2YlRCZkFlQzA3bHQ3WEdpNnkzRnZ3SHVrNHV1REF6UENJaDl1TUFRRHNEaDJsMWc9PSIsIm1hYyI6IjA2OGNhMTdhNjk5YzY1YTJlZjFhOTA5MTQ4OTNiZTBiOGM4ZmQyZmNiYjIwNThjOGQ1ZWZlOTBkODc5MWMwMmUifQ%3D%3D',
}
lat = 46.81280317947927

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive',
    'Referer': 'https://wafflehouse.locally.com/conversion?company_id=117995&inline=1&lang=en-us&is_llp_sl=true&host_domain=locations.wafflehouse.com',
    # 'Cookie': 'lg_session_v1=eyJpdiI6Inp2Qlk0TTQxVXhRZU5OZXJWUlpFRzZMQng1d0t5NGpwQkdFbEJCVkY0Q009IiwidmFsdWUiOiJcL2RMK291eWRsQ2VKTGlYT2paSTVzXC9ydW9jV3ZLQ1wvYXZvenRcL0U2YlRCZkFlQzA3bHQ3WEdpNnkzRnZ3SHVrNHV1REF6UENJaDl1TUFRRHNEaDJsMWc9PSIsIm1hYyI6IjA2OGNhMTdhNjk5YzY1YTJlZjFhOTA5MTQ4OTNiZTBiOGM4ZmQyZmNiYjIwNThjOGQ1ZWZlOTBkODc5MWMwMmUifQ%3D%3D',
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
    'store_mode': 'Closed',
    'style': '',
    'color': '',
    'upc': '',
    'category': '',
    'inline': '1',
    'show_links_in_list': '',
    'parent_domain': '',
    'map_center_lat': '46.81280317947927', # 46.81280317947927 map_center_lng=-120.02099575888789
    'map_center_lng': '-120.02099575888789',
    'map_distance_diag': '425',
    'sort_by': 'proximity',
    'no_variants': '0',
    'only_retailer_id': '',
    'dealers_company_id': '',
    'only_store_id': 'false',
    'uses_alt_coords': 'false',
    'q': 'false',
    'zoom_level': '10',
    'lang': 'en-us',
}

response = requests.get('https://wafflehouse.locally.com/stores/conversion_data', params=params, cookies=cookies, headers=headers)

locations = response.json()['markers']
print(len(locations))
for location in locations:
    # pprint(location)
    if location['status_label'] == 'Closed':
        pprint(location)

