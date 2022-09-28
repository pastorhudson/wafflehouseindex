import json
from pprint import pprint
from typing import Union

from fastapi import FastAPI
from pydantic import BaseSettings

from waffle import get_stores
import aioredis
import httpx
app = FastAPI()


class Config(BaseSettings):
    # The default URL expects the app to run using Docker and docker-compose.
    redis_url: str = 'redis://127.0.0.1:6379'



config = Config()
redis = aioredis.from_url(config.redis_url, decode_responses=True)


async def get_stores_cache():
    stores = await redis.get('stores')

    return json.loads(stores)['markers']


@app.on_event('startup')
async def startup_event():
    await redis.set('stores', json.dumps(get_stores()))


@app.get("/")
async def read_root():
    return {"stores": await get_stores_cache()}


@app.get("/stores/{store_number}")
async def read_item(store_number: int,):
    for store in await get_stores_cache():
        if store['name'].split('#')[1] == str(store_number):
            return store
    else:
        return {}


@app.get("/closed")
async def get_closed_stores():
    for store in await get_stores_cache():
        print(store['is_temporarily_closed'])
        if store['is_temporarily_closed'] is not None and store['is_temporarily_closed'] != 0:
            return store
    else:
        return {}
