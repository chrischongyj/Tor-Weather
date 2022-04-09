from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
import requests
import motor.motor_tornado
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
client = motor.motor_tornado.MotorClient(os.getenv("MONGO_URI"))
db = client['myFirstDatabase']


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


@app.get("/test")
async def test():
    return {"message": "Hello World"}


