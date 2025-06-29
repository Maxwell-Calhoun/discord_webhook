# discord_webhook

plex discord bot that will utilize a webhook for primarily intercepting plex webhooks and then using a discord bot output various webhooks

## What it does

Hosts a webhook server at endpoint localhost:8000 by default that will take in payloads from a plex server and take that payload wrangle it and then have that sent to the discord to display to others about new content availible on the server.

## How to use

Setup discord bot; learn [here](https://discordpy.readthedocs.io/en/stable/discord.html)
Setup .env using .env-template
Install Docker
Use the build-and-run.ps1 script
http://localhost:8000/test will test that api and send a test message to whatever channel you are running your discord bot in and if that isnt type ping to a channel that the bot has access to and it should reply in that channel with pong
Profit

Example of discord output:
![Example Output](image.png)

## Future implementations

I want it to be able to take a requests for content (this should be easy to do) and then ideally it grabs the content they want and adds it to the plex server (much heavier lift).
I want to add data collection for what content is being watched, when, and for how long. Then if I can collect enought (not sure if I will) then create a small ML model to determine when the server is expected to have traffic, for how long, and what type of content that might be.
