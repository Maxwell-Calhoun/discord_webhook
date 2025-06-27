import discord
import os
import threading
import asyncio
import json
import uvicorn
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn.config

# Load environment variables
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("CHANNEL_ID"))
plex_token = os.getenv("X-PLEX-TOKEN")
hostname = os.getenv("PLEX_HOSTNAME")

app = FastAPI()

# discord scripts
class MyClient(discord.Client):

    async def on_ready(self):
            print(f"✅ Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content == 'ping':
            await message.channel.send('pong')

    async def send_plex_movie_update(self, data):
        await self.wait_until_ready()
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
                    f"**Starring: **{data.get('actors', 'No tagline')}\n"
                    f"**Audience Rating: **{data.get('audience_rating', 'No tagline')}\n"
                    f"**Rating: **{data.get('content_rating', 'No tagline')} / 10\n"
                    f"**Genre: **{data.get('genres', 'No tagline')}\n"
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

async def startup():
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), client.start(discord_token))

# Test Base Root
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Test Base Root
@app.get("/test")
async def test():
    actors = ["Alden Ehrenreich", "Joonas Suotamo", "Woody Harrelson"]
    data = {
        "title" : "Solo: A Star Wars Story",
        "type" : "movie",
        "year" : "2018",
        "audience_rating" : "6.8",
        "content_rating" : "PG-13",
        "tagline" : "Never tell him the odds",
        "thumb" : "/library/metadata/7933/thumb/1750901990",
        "actors" : actors
    }

    client.loop.create_task(client.send_plex_movie_update(data))
    return {"message": "Message Sent"}

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

    try:
        if event == "library.new":
            if metadata.get("type") == "movie":
                data = wrangle_plex_new_movie_item(metadata)
                client.loop.create_task(client.send_plex_movie_update(data))
            else:
                data = wrangle_plex_new_tv_item(metadata)
                client.loop.create_task(client.send_plex_show_update(data))
            
            return {"message": "Notification sent"} 
        return {"message": f"Ignoring webhook as it is not new library {event}"}
    except Exception as e:
            return {"error": f"Failed to send message: {str(e)}"}
    

def wrangle_plex_new_movie_item(data):
    wrangled = {
        "title" : data.get("title"),
        "type" : data.get("type"),
        "tagline" : data.get("tagline"),
        "content_rating" : data.get("contentRating"),
        "audience_rating" : data.get("audienceRating"),
        "thumb" : data.get("thumb"),
        "year" : data.get("year"),
        "genres" : [genre["tag"] for genre in data.get("Genre", [])],
        "actors" : [actor["actor"] for actor in data.get("Role", [])][:3] 
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

if __name__ == "__main__":
    asyncio.run(startup())