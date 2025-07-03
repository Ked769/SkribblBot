import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import random
import re
import math


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
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

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

############################################################################TBD##
def getImage():
    """Returns a dummy image and word for skribbl"""
    # In a real implementation, this function would fetch an image and a word
    return "images/image.png", "example word"

# Refactor skribbl to accept len_game and perc
@bot.command(name='skribbl')
async def skribbl(ctx, len_game: int = 30, perc: float = None):
    ###########################
    # Constants               #
    ###########################
    image, word = getImage()
    skribbl_image_url = image
    len_word = len(''.join(i for i in word.split()))
    if perc is None:
        perc = max(0.03, 0.75 * (0.8 ** (len_word // 5)))
    time_period = len_game / ((len_word * perc).__ceil__() + 1)
    len_game += time_period # dont judge, it just wouldnt work otherwise
    total_time = 0
    ###########################

    BIG_DASH = '⬛ '
    revealed = [not ch.isalpha() for ch in word]
    display_word = lambda: ''.join(
        (ch.upper() if revealed[i] else BIG_DASH) if ch.isalpha() else "    "
        for i, ch in enumerate(word)
    )
    # Display word lengths as e.g. (5, 4) for "apple pear"
    word_lengths = "(" + ", ".join(str(len(w)) for w in word.split()) + ")"

    try:
        with open(skribbl_image_url, "rb") as f:
            msg = await ctx.send(
                f"Guess the word {word_lengths}: {display_word()}",
                file=discord.File(f, filename=os.path.basename(image))
            )
    except FileNotFoundError:
        await ctx.send("Image file not found. Please check the image path.")
        return

    unrevealed_indices = [i for i, ch in enumerate(word) if ch.isalpha() and not revealed[i]]
    total_revealable = len(unrevealed_indices)
    time_left = int(len_game)
    last_time_announce = time_left

    async def announce_time_left():
        await ctx.send(f"⏳ Time left: {time_left} seconds.")

    # for the copers
    def normalize(s):
        return re.sub(r'[^a-z0-9]', '', s.lower())

    guessed_event = asyncio.Event()
    winner = {"user": None}

    # listen for guesses
    async def guess_listener():
        while not guessed_event.is_set():
            def check(m):
                return (
                    m.channel == ctx.channel
                    and m.author != bot.user
                    and normalize(m.content) == normalize(word)
                )
            try:
                guess = await bot.wait_for('message', timeout=0.1, check=check)
                winner["user"] = guess.author
                guessed_event.set()
            except asyncio.TimeoutError:
                continue

    listener_task = asyncio.create_task(guess_listener())

    # gameloop
    max_unrevealed = math.ceil(total_revealable * (1 - perc))
    while (
        len(unrevealed_indices) > max_unrevealed
        and not guessed_event.is_set()
        and time_left > 0
    ):
        await asyncio.sleep(time_period)
        total_time += time_period
        time_left = max(0, int(time_left - time_period))

        # Announce time left every 10 seconds
        if time_left > 0 and time_left // 10 < last_time_announce // 10:
            await announce_time_left()
            last_time_announce = time_left

        if not unrevealed_indices:
            break

        idx = random.choice(unrevealed_indices)
        revealed[idx] = True
        unrevealed_indices.remove(idx)

        try:
            await msg.edit(content=f"Guess the word {word_lengths}: {display_word()}")
        except discord.NotFound:
            await ctx.send("Message not found or has been deleted.")
            break

    # End the listener task
    guessed_event.set()
    await listener_task

    if winner["user"]:
        await ctx.send(f"🎉 {winner['user'].mention} guessed the word: {word.upper()}!")
    elif not unrevealed_indices:
        await ctx.send(f"Game over! The word was: {word.upper()}")
    elif time_left <= 0:
        await ctx.send(f"⏰ Time's up! The word was: {word.upper()}")

# Add the slash command
@bot.tree.command(
    name="skribbl",
    description="Start a skribbl game. Optionally set game time and percent to reveal."
)
@app_commands.describe(
    length="Total time in seconds for the game (default: 30)",
    perc="Fraction (0-1) of the word to reveal before ending (default: auto)"
)
async def skribbl_slash(
    interaction: discord.Interaction,
    length: int = 30,
    perc: float = None
):
    """Slash command for skribbl with optional time and perc."""
    await interaction.response.defer()
    ctx = await bot.get_context(interaction)
    await skribbl(ctx, len_game=length, perc=perc)

# Begin chutiyapa
if __name__ == '__main__':
    bot.run(TOKEN)

else:
    print("This script is not meant to be imported as a module.")
    print("Please run it directly to start the bot.")