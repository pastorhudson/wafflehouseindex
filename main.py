import json
from pydantic import BaseSettings
from waffle import get_stores
import aioredis
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

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
    stores = await redis.get('stores')

    return json.loads(stores)['markers']


@app.on_event('startup')
@repeat_every(seconds=300)  # 5 min
async def startup_event():
    await redis.set('stores', json.dumps(get_stores()))


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/stores")
async def read_stores():
    return {"stores": await get_stores_cache()}


@app.get("/store/{store_number}")
async def read_item(store_number: int,):
    for store in await get_stores_cache():
        if store['name'].split('#')[1] == str(store_number):
            return store
    else:
        return {}


@app.get("/stores/closed")
async def get_closed_stores():
    for store in await get_stores_cache():
        print(store['is_temporarily_closed'])
        if store['is_temporarily_closed'] is not None and store['is_temporarily_closed'] != 0:
            return store
    else:
        return {}
