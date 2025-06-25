import discord
import os
import threading
import asyncio
import json
from fastapi import FastAPI, Request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("CHANNEL_ID"))
plex_token = os.getenv("X-PLEX-TOKEN")
hostname = os.getenv("PLEX_HOSTNAME")

# discord scripts

class MyClient(discord.Client):

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content == 'ping':
            await message.channel.send('pong')

    async def send_plex_update(self):
        print("Sending log")
        channel = self.get_channel(channel_id)
        if channel is None:
            print("Channel not found. Bot may not have access or isn't in the server.")
            return
        await channel.send("TEST")


# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

# Thread for the discord client
discord_thread = threading.Thread(target=lambda: client.run(discord_token), daemon=True)
discord_thread.start()

# API Under Here
app = FastAPI()
    
# Test Base Root
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Will take in plex data and handle that to allow the discord bot to post appropriately
# TODO: need to proper web reponses later thiis will do for now
@app.post("/plex")
async def plex(request: Request):
    #print(await request.body)
    form = await request.form()
    print("Form keys:", list(form.keys()))
    payload = form.get("payload")
    if payload is None:
        print("ERROR: No payload found in form data.")
        return {"error": "No payload found"}

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print("ERROR: Invalid JSON in payload.")
        return {"error": "Invalid JSON"}

    event = data.get("event")
    metadata = data.get("Metadata")

    print("Event:", event)

    if event == "re":
        future = asyncio.run_coroutine_threadsafe(client.send_plex_update(), client.loop)
        
        try:
            future.result(timeout=10)
            return {"message": "Notification sent"}
        except Exception as e:
            return {"error": f"Failed to send message: {str(e)}"}
    else:
        try:
            
            return {"message": "Ignoring due to wrong event"}
        except Exception as e:
            print(e)
    