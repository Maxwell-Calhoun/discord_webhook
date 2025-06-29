# Plex Discord Webhook Bot

A Discord bot that listens for webhooks from your Plex server and sends notifications to a Discord channel when new content is added.

---

## What It Does

- Hosts a FastAPI webhook server at `http://localhost:8000` (by default)
- Accepts incoming Plex `library.new` webhooks
- Wrangles the data
- Sends a notification to a configured Discord channel with info about the new content that is now hosted on Plex

---

## How to Use

1. **Set up a Discord Bot**

   - Follow the guide here: [discord.py setup](https://discordpy.readthedocs.io/en/stable/discord.html)

2. **Configure `.env`**

   - Copy `.env-template` → `.env`
   - Fill in your Discord bot token, channel ID, Plex token, etc.

3. **Install Docker**
   - [Download Docker Here](https://docs.docker.com/engine/install/)
   - If on windows you will probably want WSL as well
4. **Run the Bot**

   - If on windows you can use the included PowerShell script:

     ```powershell
     ./build-and-run.ps1
     ```

   - Otherwise use docker build and run to run the container with the provided dockerfile
   - You can also run outside container using py ./main.py make sure to install requirements from requirements.txt

5. **Test**

   - Open or use Postman: http://localhost:8000/test

   - This sends a test message to your configured Discord channel.

   - Or, in any channel the bot has access to send `ping` and the bot should respond with `pong`

---

## Example Output

Example of discord output:
![Example Output](discord_embed.png)

## Future Implementations

- Configure for more webhook data to come in a process that data

- Let users request content in Discord (easy lift)

- Automatically add requested content to Plex (longer-term goal)

- Track viewing data: what's watched, when, and for how long

- Use basic ML to:

  - Predict when server traffic will spike

  - Estimate what kind of content will be popular
