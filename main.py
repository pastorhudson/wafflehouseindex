import json
from pydantic import BaseSettings
from waffle import get_stores, write_stores, get_closed_stores_cache
import aioredis
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
from fastapi_pagination import Page, add_pagination, paginate, Params

description = """
Waffle House Index API helps show what Waffle Houses are closed in natural disasters.
"""

app = FastAPI(title="Waffle House Index API",
              description=description,
              version="0.0.1",
              # terms_of_service="http://example.com/terms/",
              # contact={
              #     "name": "Deadpoolio the Amazing",
              #     "url": "http://x-force.example.com/contact/",
              #     "email": "dp@x-force.example.com",
              # },
              # license_info={
              #     "name": "Apache 2.0",
              #     "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
              # },
              )
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class Config(BaseSettings):
    # The default URL expects the app to run using Docker and docker-compose.
    redis_url: str = 'redis://127.0.0.1:6379'


config = Config()
redis = aioredis.from_url(config.redis_url, decode_responses=True)


async def get_stores_cache():
    stores = json.loads(await redis.get('stores'))
    return stores['markers']


@app.on_event('startup')
@repeat_every(seconds=60 * 60)  # 1 hour
async def startup_event():
    await redis.delete('_stores')
    await redis.delete('stores')
    await redis.set('stores', json.dumps(await get_stores()))

    await write_stores(redis)


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request,
                                                     "closed_stores": await get_closed_stores_cache(redis)})


@app.get("/cache", include_in_schema=False)
async def cache_dump(request: Request):
    return json.loads(await redis.get('_stores'))


@app.get("/reset_2760792038", include_in_schema=False)
async def cache_reset(request: Request):
    await redis.delete('_stores')
    await redis.delete('stores')
    await redis.delete('stores_status')

    return {"Reset": 'success'}


@app.get("/stores", response_model=Page[dict])
async def read_stores(state: str = None, params: Params = Depends()):
    stores = await get_stores_cache()
    filter_stores = []
    if state:
        for store in stores:
            if store['state'].lower() == state.lower():
                filter_stores.append(store)
        return paginate(filter_stores, params)
    return paginate(stores, params)


@app.get("/store/{store_number}")
async def read_item(store_number: int,):
    for store in await get_stores_cache():
        if store['name'].split('#')[1] == str(store_number):
            return store
    else:
        return {}


@app.get("/stores/closed")
async def get_closed_stores():
    closed_stores = []
    try:
        for store in json.loads(await redis.get('stores_status')):
            if "closed" in store['Status'].lower():
            # if store["sun_time_open"] == 0 or store["sun_time_close"] == 0 or store["mon_time_open"] == 0 or store["mon_time_close"] == 0 or store["tue_time_open"] == 0 or store["tue_time_close"] == 0 or store["wed_time_open"] == 0 or store["wed_time_close"] == 0 or store["thu_time_open"] == 0 or store["thu_time_close"] == 0 or store["fri_time_open"] == 0 or store["fri_time_close"] == 0 or store["sat_time_open"] == 0 or store["sat_time_close"] == 0:
                closed_stores.append(store)
    except TypeError:
        closed_stores = {"Still Caching": True}
    return set(closed_stores)
