import json
from datetime import datetime

from pydantic import BaseSettings
from waffle import get_stores, write_stores, get_closed_stores_cache, get_all_stores_cache
import aioredis
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
from us_state_abbrev import abbrev_to_us_state


description = """
Waffle House Index API helps show what Waffle Houses are closed in natural disasters.
"""

app = FastAPI(title="Waffle House Index API",
              description=description,
              version="0.0.1",
              )
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class Config(BaseSettings):
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
    await redis.delete('percent_complete')
    await redis.set('stores', json.dumps(await get_stores()))
    await write_stores(redis)


@app.get("/", include_in_schema=False)
async def root(request: Request, state: str = None):
    stores = await get_closed_stores_cache(redis)
    filter_stores = []
    if state:
        for store in stores['stores']:
            if store['state'].lower() == state.lower():
                filter_stores.append(store)
        return templates.TemplateResponse('index.html', {
            "request": request,
            "closed_stores": {"stores": filter_stores,
                              "last_updates": stores['last_updates'],
                              "current_progress": stores['current_progress'],
                              },
            "state": abbrev_to_us_state[state.upper()],
            "states": abbrev_to_us_state
        })
    stores['state'] = None
    return templates.TemplateResponse("index.html", {"request": request,
                                                     "closed_stores": stores,
                                                     "state": None,
                                                     "states": abbrev_to_us_state})


@app.get("/percent_complete", include_in_schema=False)
async def percent_complete(request: Request):
    try:
        return json.loads(await redis.get('store_status_percent'))
    except ValueError:
        progress = {"total": None,
                    "current": None,
                    "percent_complete": None}
        return progress


@app.get("/hx_progress", include_in_schema=False)
async def hxprogress(request: Request):
    try:
        progress = json.loads(await redis.get('store_status_percent'))
        return templates.TemplateResponse("partials/progress.html", {"request": request,
                                                                     "percent_complete": progress['percent_complete'],
                                                                     "last_update": datetime.utcnow()})

    except ValueError:
        progress = {
                    "percent_complete": None,
                    "last_update": datetime.utcnow()
        }
        return templates.TemplateResponse("partials/progress.html", {"request": request,
                                                                     "percent_complete": progress['percent_complete'],
                                                                     "last_update": progress['last_update']})


@app.get("/cache", include_in_schema=False)
async def cache_dump(request: Request):
    return json.loads(await redis.get('_stores'))


@app.get("/reset_2760792038", include_in_schema=False)
async def cache_reset(request: Request):
    await redis.delete('_stores')
    await redis.delete('stores')
    await redis.delete('stores_status')

    return {"Reset": 'success'}


@app.get("/stores")
async def read_stores(state: str = None, page: int = 0, limit: int = 50):
    stores = await get_all_stores_cache(redis)
    filter_stores = []
    if state:
        for store in stores['stores']:
            if store['state'].lower() == state.lower():
                filter_stores.append(store)
        return {"stores": filter_stores,
                "last_updates": stores['last_updates'],
                "current_progress": stores['current_progress']}

    if not page and not state:
        return {"stores": stores['stores'][0:50],
                "last_updates": stores['last_updates'],
                "current_progress": stores['current_progress']}
    elif not page and state:
        return {"stores": filter_stores[0:50],
                "last_updates": stores['last_updates'],
                "current_progress": stores['current_progress']}

    if page:
        try:
            page_offset = page * 50
            return {"stores": stores[0:page_offset],
                    "last_updates": stores['last_updates'],
                    "current_progress": stores['current_progress']}
        except TypeError:
            pass

    return stores


@app.get("/store/{store_number}")
async def read_item(store_number: int,):
    for store in await get_stores_cache():
        if store['name'].split('#')[1] == str(store_number):
            return store
    else:
        return {}


@app.get("/stores/closed")
async def get_closed_stores(state: str = None):
    stores = await get_closed_stores_cache(redis)
    filter_stores = []
    if state:
        for store in stores['stores']:
            if store['state'].lower() == state.lower():
                filter_stores.append(store)
        return {"stores": filter_stores,
                "last_updates": stores['last_updates'],
                "current_progress": stores['current_progress']}
    return await get_closed_stores_cache(redis)
