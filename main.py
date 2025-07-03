import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))  # Default to 0 if not set

# Check if the token is provided
if not TOKEN:
    raise ValueError("No DISCORD_TOKEN found in .env file")

# Create a bot instance with command prefix
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    print(f"synced commands: {len(bot.commands)}")
@bot.event
async def on_command_error(ctx, error):
    """Handles command errors."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Please check the command name.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. Please provide all necessary arguments.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")
        raise error
    
@bot.event
async def on_message(message):
    """Handles incoming messages."""
    if message.author == bot.user:
        return
    # Process commands if the message starts with the command prefix
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)

@bot.command(name='ping')
async def ping(ctx):
    """Responds with 'Pong!'."""
    await ctx.send('Pong!')

def getImage():
    """Returns a dummy image and word for skribbl.io game."""
    # In a real implementation, this function would fetch an image and a word
    return "images/image.png", "example_word"

@bot.command(name='skribbl')
async def skribbl(ctx):
    """Sends an image of a skribbl.io game and starts guessing game."""
    image, word = getImage()
    skribbl_image_url = "https://example.com/skribbl_image.png"  # Replace with actual image URL
    await ctx.send(
        "Guess the word : " + '_' * len(word),
        file=discord.File(skribbl_image_url, filename=image)
    )
    

# Run the bot with the token
if __name__ == '__main__':
    bot.run(TOKEN)

else:
    print("This script is not meant to be imported as a module.")
    print("Please run it directly to start the bot.")