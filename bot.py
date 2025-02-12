import discord
from google import genai
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv('abc.env')

# Set up the bot client with the correct intents
intents = discord.Intents.default()
intents.message_content = True  # Allow the bot to read message content
client = discord.Client(intents=intents)

# Get the environment variables
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("Error: Missing required tokens in .env file.")
    exit()

# Initialize the Gemini client
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Store the allowed channel ID (default is None)
allowed_channel_id = None

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    global allowed_channel_id  # Allow modification of the variable

    # Don't let the bot respond to itself
    if message.author == client.user:
        return

    # Handle custom !commands separately
    if message.content.startswith("!"):
        command_parts = message.content.split()

        if command_parts[0] == "!configure":
            if len(command_parts) == 2:
                channel_mention = command_parts[1]

                # Extract channel ID from mention (e.g., <#123456789012345678>)
                match = re.match(r"<#(\d+)>", channel_mention)
                if match:
                    allowed_channel_id = int(match.group(1))
                elif channel_mention.isdigit():
                    allowed_channel_id = int(channel_mention)
                else:
                    await message.reply("⚠️ Invalid format. Use `!configure <channel_id>` or mention a channel like `!configure #general`.")
                    return
                
                await message.reply(f"✅ Bot is now configured to work only in <#{allowed_channel_id}>")
            else:
                await message.reply("⚠️ Invalid command format. Use `!configure <channel_id>` or mention a channel like `!configure #general`.")
        elif command_parts[0] == "!projectabout":
            embed = discord.Embed(
                title="🤖 Mastixia - The AI Assistant",
                description="Mastixia is a bot powered by Gemini AI, designed to provide intelligent responses, automate tasks, and enhance user engagement in Discord communities. From answering questions to managing discussions, Mastixia ensures a smooth and interactive experience.",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Built for intelligent conversations! 🚀")
            await message.reply(embed=embed)  # Use reply format
        return  

    # If a channel is configured, only respond in that channel
    if allowed_channel_id and message.channel.id != allowed_channel_id:
        return  # Ignore messages from other channels

    print(f"Received message: {message.content}")

    try:
        # Modify the message before sending it to the API
        modified_prompt = f"{message.content} (within 200 words)"

        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[modified_prompt]  # Send the modified prompt to the API
        )
        reply = response.text.strip()  # Get the response

        if not reply:  # If empty, return a fallback message
            await message.reply("I couldn't generate a response.")  # Use reply format
            return

        # Ensure the reply does not exceed Discord's 2000-character limit
        final_reply = reply[:2000]

        await message.reply(final_reply)  # Reply directly to the user
    except Exception as e:
        await message.reply("Something went wrong.")  # Reply format
        print(f"Error: {e}")

# Run the bot
client.run(DISCORD_TOKEN)
