# discord_webhook

plex discord bot that will utilize a webhook for primarily intercepting plex webhooks and then using a discord bot output various webhooks

## What it does

Hosts a webhook server at endpoint localhost:8000 by default that will take in payloads from a plex server and take that payload wrangle it and then have that sent to the discord to display to others about new content availible on the server.

## Future implementation

I want it to be able to take a requests for content (this should be easy to do) and then ideally it grabs the content they want and adds it to the plex server (much heavier lift).
I want to add data collection for what content is being watched, when, and for how long. Then if I can collect enought (not sure if I will) then create a small ML model to determine when the server is expected to have traffic, for how long, and what type of content that might be.
