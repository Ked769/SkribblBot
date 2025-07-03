import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import random
import string

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
    return "images/image.png", "example word"

@bot.command(name='skribbl')
async def skribbl(ctx):
    """Sends an image of a skribbl.io game and starts guessing game, revealing a random letter every 30 seconds."""
    image, word = getImage()
    skribbl_image_url = image
    BIG_DASH = '⬛ '
    revealed = [not ch.isalpha() for ch in word]
    display_word = lambda: ''.join(
        (ch.upper() if revealed[i] else BIG_DASH) if ch.isalpha() else ch
        for i, ch in enumerate(word)
    )
    try:
        with open(skribbl_image_url, "rb") as f:
            msg = await ctx.send(
                f"Guess the word : {display_word()}",
                file=discord.File(f, filename=os.path.basename(image))
            )
    except FileNotFoundError:
        await ctx.send("Image file not found. Please check the image path.")
        return

    unrevealed_indices = [i for i, ch in enumerate(word) if ch.isalpha() and not revealed[i]]

    while unrevealed_indices:
        ##########################
        time_period = 1          # debug
        ##########################
        await asyncio.sleep(time_period)
        idx = random.choice(unrevealed_indices)
        revealed[idx] = True
        unrevealed_indices.remove(idx)

        def check(m):
            return (
                m.channel == ctx.channel
                and m.author != bot.user
                and m.content.strip().lower() == word.lower()
            )
        try:
            guess = await bot.wait_for('message', timeout=time_period, check=check)
            await ctx.send(f"🎉 {guess.author.mention} guessed the word: {word.upper()}!")
            break
        except asyncio.TimeoutError:
            pass

        try:
            await msg.edit(content=f"Guess the word : {display_word()}")
        except discord.NotFound:
            await ctx.send("Message not found or has been deleted.")
            break  # Message deleted or not found
        if not unrevealed_indices:
            await ctx.send(f"Game over! The word was: {word.upper()}")
            break
    

# Run the bot with the token
if __name__ == '__main__':
    bot.run(TOKEN)

else:
    print("This script is not meant to be imported as a module.")
    print("Please run it directly to start the bot.")