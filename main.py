import discord
import os
import asyncio
import json
import uvicorn
from fastapi import FastAPI, Request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("CHANNEL_ID"))
plex_token = os.getenv("X-PLEX-TOKEN")
hostname = os.getenv("PLEX_HOSTNAME")
thumbnail_url = os.getenv("THUMBNAIL_URL")
port = os.getenv("PORT")

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

    async def send_plex_new_content(self, data):
        await self.wait_until_ready()
        print("Sending log")
        channel = self.get_channel(channel_id)
        if channel is None:
            print("Channel not found. Bot may not have access or isn't in the server.")
            return

        thumb_url = f"https://{hostname}{data['thumb']}?X-Plex-Token={plex_token}"
        
        if (data['type'] == "movie"):
            embed = discord.Embed(
                title=f"New {data['type']} to goon to!",
                colour=discord.Colour.dark_teal(),
                description=(
                        f"**Title: **{data['title']}\n"
                        f"**Tag: **{data.get('tagline', 'N/A')}\n"
                        f"**Starring: **{data['actors']}\n"
                        f"**Audience Rating: **{data.get('audience_rating', 'N/A')}\n"
                        f"**Rating: **{data.get('content_rating', 'N/A')} / 10\n"
                        f"**Genre: **{data.get('genres', 'N/A')}\n"
            ))
        else:
            embed = discord.Embed(
                title=f"New {data['type']} to goon to!",
                colour=discord.Colour.dark_teal(),
                description=(
                        f"**Title: **{data['grandparentTitle']}\n"
                        f"**Episode: **S{data['season']:02}E{data['episode']:02}: {data['grandparentTitle']}\n"
                        f"**Summary: **{data.get('summary', 'N/A')}\n"
                        f"**Starring: **{data.get('actors', 'N/A')}\n"
                        f"**Audience Rating: **{data.get('audience_rating', 'N/A')}\n"
                        f"**Rating: **{data.get('content_rating', 'N/A')} / 10\n"
                        f"**Air Date:** {data['air_date']} | "
                        f"**Duration:** {data['duration']} min"
            ))
        
        embed.set_footer(text="Plex Library • GoonBox")
        # set image give larger image than thumbnail
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_image(url=thumb_url)
        await channel.send(embed=embed)
        print("Embed sent.")

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

async def startup():
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
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
        "audience_rating" : "6.6",
        "content_rating" : "PG-13",
        "tagline" : "Never tell him the odds",
        "thumb" : "/library/metadata/8008/thumb/1750992579",
        "actors" : actors
    }

    client.loop.create_task(client.send_plex_new_content(data))
    return {"message": "Message Sent"}

# Will take in plex data and handle that to allow the discord bot to post appropriately
# TODO: need to proper web reponses later thiis will do for now
@app.post("/plex")
async def plex(request: Request):
    form = await request.form()
    print(form)
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
            else:
                data = wrangle_plex_new_tv_item(metadata)
            
            client.loop.create_task(client.send_plex_new_content(data))
            
            return {"message": "Notification sent"} 
        return {"message": f"Ignoring webhook as it is not new library {event}"}
    except Exception as e:
            return {"error": f"Failed to send message: {str(e)}"}
    

# TODO: Combine the data handling as it doesnt need to be two seperate functions just handle the data potentially not being there
def wrangle_plex_new_movie_item(data):
    actors = ", ".join([actor["tag"] for actor in data.get("Role", [])][:3])
    return {
        "title" : data.get("title"),
        "type" : data.get("type"),
        "tagline" : data.get("tagline"),
        "content_rating" : data.get("contentRating"),
        "audience_rating" : data.get("audienceRating"),
        "thumb" : data.get("thumb"),
        "year" : data.get("year"),
        "genres" : [genre["tag"] for genre in data.get("Genre", [])],
        "actors": actors if actors else "N/A"
    }

def wrangle_plex_new_tv_item(data):
    actors = ", ".join([actor["tag"] for actor in data.get("Role", [])][:3])
    return {
        "type": data.get("type"),
        "season": data.get("parentIndex") or "N/A",
        "episode": data.get("index") or "N/A",
        "grandparentTitle": data.get("grandparentTitle") or data.get("title") or "N/A",
        "summary": data.get("summary", "N/A"),
        "audience_rating" : data.get("audienceRating", "N/A"),
        "content_rating": data.get("contentRating", "N/A"),
        "air_date": data.get("originallyAvailableAt", "N/A"),
        "duration": round(int(data.get("duration", 0)) / 60000),  # ms → min
        "thumb": data.get("thumb", data.get("grandparentThumb")),
        "actors": actors if actors else "N/A"
    }

if __name__ == "__main__":
    asyncio.run(startup())