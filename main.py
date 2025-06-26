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

    async def send_plex_movie_update(self, data):
        print("Sending log")
        channel = self.get_channel(channel_id)
        if channel is None:
            print("Channel not found. Bot may not have access or isn't in the server.")
            return

        thumb_url = f"https://{hostname}{data['thumb']}?X-Plex-Token={plex_token}"

        embed = discord.Embed(
            title=f"New {data['type']} to goon to!",
            colour=discord.Colour.dark_teal(),
            description=(
                    f"**Title: **{data['title']}\n"
                    f"**Tag: **{data.get('tagline', 'No tagline')}\n"
                    f"**Tear: **{data.get('audience_rating', 'No tagline')}\n"
                    f"**Rating: **{data.get('content_rating', 'No tagline')}\n"
                    f"**Genre: **{data.get('genre', 'No tagline')}\n"

        ))

        #embed.add_field(
        #    name="Starring",
        #    value=', '.join(data.get('actors', [])) or "N/A",
        #    inline=False
        #)
        
        embed.set_footer(text="Plex Library • GoonBox")
        # set image give larger image than thumbnail
        embed.set_image(url=thumb_url)
        await channel.send(embed=embed)
        print("Embed sent.")


    # TODO: Implement this for shows        
    async def send_plex_show_update(self, data):
        print("Sending log")
        channel = self.get_channel(channel_id)
        if channel is None:
            print("Channel not found. Bot may not have access or isn't in the server.")
            return
        message = "New " + data["type"] + " to goon to " + data["title"] + "! " + hostname + data["thumb"] + plex_token
        await channel.send(embed=message)


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

# Test Base Root
@app.get("/test")
async def root():
    data = {
        "title" : "Solo: A Star Wars Story",
        "type" : "movie",
        "year" : "2018",
        "audience_rating" : "6.8",
        "content_rating" : "PG-13",
        "tagline" : "Never tell him the odds",
        "thumb" : "/library/metadata/7933/thumb/1750901990",
    }
    asyncio.run_coroutine_threadsafe(client.send_plex_movie_update(data), client.loop)
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

    if event == "library.new":
        if metadata.get("type") == "movie":
            data = wrangle_plex_new_movie_item(metadata)
            future = asyncio.run_coroutine_threadsafe(client.send_plex_movie_update(data), client.loop)
        else:
            data = wrangle_plex_new_tv_item(metadata)
            future = asyncio.run_coroutine_threadsafe(client.send_plex_show_update(data), client.loop)
        
        
        
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


def wrangle_plex_new_movie_item(data):
    wrangled = {
        "title" : data.get("title"),
        "type" : data.get("type"),
        "tagline" : data.get("tagline"),
        "content_rating" : data.get("contentRating"),
        "audience_rating" : data.get("audienceRating"),
        "thumb" : data.get("thumb"),
        "year" : data.get("year")
    }
    return wrangled

def wrangle_plex_new_tv_item(data):
    wrangled = {
        "title" : data.get("title"),
        "type" : data.get("type"),
        "thumb" : data.get("thumb"),
        "year" : data.get("year")
    }
    return wrangled