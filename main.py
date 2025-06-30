import discord
import os
import asyncio
import json
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("CHANNEL_ID"))
test_channel_id = int(os.getenv("TEST_CHANNEL_ID"))
plex_token = os.getenv("X-PLEX-TOKEN")
hostname = os.getenv("PLEX_HOSTNAME")
thumbnail_url = os.getenv("THUMBNAIL_URL")
port = int(os.getenv("PORT"))

app = FastAPI()

# discord scripts
class MyClient(discord.Client):

    async def on_ready(self):
            print(f"✅ Logged in as {self.user} (ID: {self.user.id})")

    # I just use this to check the discord bot is actually running properly
    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content == 'ping':
            await message.channel.send('pong')

    async def send_plex_new_content(self, data, server, channel_override=None):
        await self.wait_until_ready()
        # in the case where we want to test we can setup test channel and set that as override on call
        if channel_override is None:
            channel = self.get_channel(channel_id)
        else:
            channel = self.get_channel(channel_override)
        
        if channel is None:
            print("Channel not found. Bot may not have access or isn't in the server.")
            return

        thumb_url = f"https://{hostname}{data['thumb']}?X-Plex-Token={plex_token}"
        content_url = f"https://{hostname}/web/index.html#!/server/{server.get('uuid')}/details?key=/library/metadata/{data.get('ratingKey')}"

        if (data['type'] == "movie"):
            embed = discord.Embed(
                title=f"NEW {data['type'].upper()} TO GOON TO",
                url=content_url,
                colour=discord.Colour.dark_teal(),
                description=(
                        f"**Title: **{data['title']}\n"
                        f"**Tag: **{data.get('tagline', 'N/A')}\n"
                        f"**Starring: **{data['actors']}\n"
                        f"**Runtime: **{data['duration']}\n"
                        f"**Audience Rating: **{data.get('audience_rating', 'N/A')}\n"
                        f"**Rating: **{data.get('content_rating', 'N/A')}\n"
                        f"**Genre: **{data.get('genres', 'N/A')}\n"
            ))
        else:
            # condition where input is not an episode but rather new show
            if data['season'] is not None or data['episode'] is not None:
                episode = f"**Episode: **S{data['season']:02}E{data['episode']:02}: {data['title']}\n"
            else:
                episode = ""

            embed = discord.Embed(
                title=f"NEW {data['type'].upper()} TO GOON TO",
                colour=discord.Colour.dark_teal(),
                url=content_url,
                description=(
                        f"**Title: **{data['title']}\n"
                        f"{episode}"
                        f"**Starring: **{data.get('actors', 'N/A')}\n"
                        f"**Audience Rating: **{data.get('audience_rating', 'N/A')}\n"
                        f"**Rating: **{data.get('content_rating', 'N/A')}\n"
                        f"**Air Date:** {data['air_date']} | "
                        f"**Duration:** {data['duration']}"
            ))
        
        embed.set_footer(text=f"Plex Library • {hostname}")

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
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), client.start(discord_token))

# Test Base Root
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Test Base Root; should technically be post but I want to easily test and this is fine
@app.get("/test")
async def test():
    actors = ", ".join(["Alden Ehrenreich", "Joonas Suotamo", "Woody Harrelson"][:3])
    genres = ", ".join(["action", "adventure", "mystery"][:3])
    data = {
        "title" : "Solo: A Star Wars Story",
        "type" : "movie",
        "year" : "2018",
        "audience_rating" : "6.6",
        "content_rating" : "PG-13",
        "tagline" : "Never tell him the odds",
        "duration" : f"{round(8100000/60000)} mins",
        "thumb" : "/library/metadata/8008/thumb/1750992579",
        "ratingKey" : "8008",
        "genres" : genres,
        "actors" : actors
    }

    server = {
        "title": "Test",
        "uuid": "7ccb25ef9967c0387943dd18e1bda78ef722d635"
    }
    
    client.loop.create_task(client.send_plex_new_content(data, server, channel_override=test_channel_id))
    return {"message": "Message Sent"}

# Will take in plex data and handle that to allow the discord bot to post appropriately
# TODO: need to proper web reponses later thiis will do for now
@app.post("/plex")
async def plex(request: Request):
    form = await request.form()
    # printing payload for potential debugging and logging
    print(form)
    payload = form.get("payload")
    if payload is None:
        print("ERROR: No payload found in form data.")
        raise HTTPException(status_code=400, detail=f"No payload data found")

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print("ERROR: Invalid JSON in payload.")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {payload}")

    event = data.get("event")
    metadata = data.get("Metadata")
    server = data.get("Server")

    try:
        # library.new would include new movie, show (multiple episodes), and new episodes as well other content that I dont personally host like music
        if event == "library.new":
            print("here1")
            data = wrangle_plex_payload(metadata)
            print("here2")
            client.loop.create_task(client.send_plex_new_content(data, server))
            
            return {"message": "Notification sent"} 
        return {"message": f"Ignoring webhook as it is not new library {event}"}
    except Exception as e:
        print(f"ERROR: Failed to send message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

def wrangle_plex_payload(data):
    actors = ", ".join([actor["tag"] for actor in data.get("Role", [])][:3])
    genres = ", ".join([genre["tag"] for genre in data.get("Genre", [])][:3])
    return {
        "title": data.get("grandparentTitle") or data.get("title") or "N/A",
        "type": data.get("type"),
        "season": data.get("parentIndex") or "N/A",
        "episode": data.get("index") or "N/A",
        "tagline" : data.get("tagline") or "N/A",
        "summary": data.get("summary") or "N/A",
        "audience_rating": f"{data['audienceRating']}/10" if data.get("audienceRating") is not None else "N/A",
        "content_rating": data.get("contentRating") or  "N/A",
        "air_date": data.get("originallyAvailableAt") or  "N/A",
        "duration": "N/A" if int(data.get("duration", 0)) == 0 else f"{round(int(data['duration']) / 60000)} mins", # ms -> mins
        "thumb": data.get("thumb", data.get("grandparentThumb")) or  "N/A",
        "year" : data.get("year") or "N/A",
        "ratingKey" : data.get("ratingKey") or "N/A",
        "genres": genres if genres else "N/A",
        "actors": actors if actors else "N/A"
    }

if __name__ == "__main__":
    asyncio.run(startup())