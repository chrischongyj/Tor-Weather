from fastapi import FastAPI, Request
from fastapi_utils.tasks import repeat_every
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
import motor.motor_tornado
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
client = motor.motor_tornado.MotorClient(os.getenv("MONGO_URI"))
db = client['myFirstDatabase']

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
@repeat_every(seconds=60*60)
async def get_onionoo():
    print("Getting onionoo data...")
    response = requests.get("https://onionoo.torproject.org/details")
    data = response.json()

    for relay in data['relays']:
        if await db.relays.find_one({'fingerprint': relay['fingerprint']}):
            await db.relays.update_one({'fingerprint': relay['fingerprint']}, {'$set': relay})
        else:
            await db.relays.insert_one(relay)
    print("Done.")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get("/fingerprint/{id}", response_class=HTMLResponse)
async def get_relay_info(request: Request, id: str):
    relay_info = await db.relays.find_one({'fingerprint': id})
    if relay_info:
        relay_running = bool(relay_info.get('running', False))
    else:
        relay_running = False
    return templates.TemplateResponse("relay.html", {"request": request, "relay_info": relay_info, "relay_running": relay_running})