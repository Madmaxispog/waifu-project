import discord
from discord.ext import commands
import requests
import asyncio
from discord import Embed
import aiohttp
from aiohttp import TCPConnector
from typing import Optional

# Set up intents
intents = discord.Intents.all()
intents.message_content = True 

# Initialize bot
bot = commands.Bot(command_prefix='~', intents=intents)
bot.remove_command('help')

# Constants
TOKEN = 'MTMyNjU3MjM3MDMzMjM1NjY3OA.G7KkKj.RYUoMoaqPnNMdWToYMAwz0sicHp513KkG3YhVA'  
PROXY_URL = "http://159.65.170.68:80"  # Add proxy URL
ENDPOINTS = {
    'sfw': 'https://api.waifu.pics/sfw/waifu',
    'nsfw': 'https://api.waifu.pics/nsfw/waifu'
}
current_endpoint = ENDPOINTS['sfw']

# Global session variable
session: Optional[aiohttp.ClientSession] = None

@bot.event
async def on_ready():
    global session
    try:
        # Initialize connector and session when bot is ready
        connector = TCPConnector(
            ssl=False,  # Updated from verify_ssl
            use_dns_cache=True
        )
        session = aiohttp.ClientSession(
            connector=connector,
            trust_env=True,
            headers={'HTTPS': PROXY_URL}
        )
        print(f"{bot.user.name} is ready!")
        bot.loop.create_task(change_status())
    except Exception as e:
        print(f"Failed to initialize session: {e}")
        await bot.close()

# Add cleanup
async def cleanup():
    global session
    if session and not session.closed:
        await session.close()
        session = None

async def change_status():
    while True:
        total_members = sum(guild.member_count or 0 for guild in bot.guilds)
        activities = [
            discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{total_members} users :)"
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(bot.guilds)} servers :)"
            )
        ]
        for activity in activities:
            await bot.change_presence(activity=activity)
            await asyncio.sleep(15)

@bot.command()
async def sfw(ctx):
    global current_endpoint
    current_endpoint = ENDPOINTS['sfw']
    await ctx.send('Switched to SFW mode.')

@bot.command()
async def nsfw(ctx):
    global current_endpoint
    current_endpoint = ENDPOINTS['nsfw']
    await ctx.send('Switched to NSFW mode.')

# Update waifu command to use proxy
@bot.command()
async def waifu(ctx):
    try:
        async with ctx.typing():
            async with session.get(current_endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data['url']
                    
                    embed = Embed(title="Here you go~ <3", color=discord.Color.purple())
                    embed.set_image(url=image_url)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"An error occurred: {response.status}")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command()
async def botinfo(ctx):
    latency = round(bot.latency * 1000)
    member_count = len([m for m in ctx.guild.members if not m.bot])
    bot_count = len([m for m in ctx.guild.members if m.bot])
    
    embed = Embed(title=f"{bot.user.name} Details", color=discord.Color.blue())
    embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
    embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
    embed.add_field(name="Bot Latency", value=f"{latency} ms", inline=True)
    embed.add_field(name="Member Count", value=member_count, inline=True)
    embed.add_field(name="Bot Count", value=bot_count, inline=True)
    
    await ctx.send(embed=embed)

# Add new purge command
@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = None):
    if amount is None:
        await ctx.send("Please specify the number of messages to delete.")
        return
    
    if amount <= 0:
        await ctx.send("Please specify a positive number of messages to delete.")
        return
    
    if amount > 1000:
        await ctx.send("You can only delete up to 1000 messages at a time.")
        return
    
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include command message
        confirmation = await ctx.send(f"Deleted {len(deleted) - 1} messages.")
        await asyncio.sleep(2)
        await confirmation.delete()
    except discord.Forbidden:
        await ctx.send("I don't have permission to delete messages.")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while deleting messages: {str(e)}")

# Error handling for cooldown
@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        remaining = round(error.retry_after, 1)
        await ctx.send(f"Please wait {remaining} seconds before purging again.", delete_after=5)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.", delete_after=5)

# help command
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Help Menu",
        description="Need help? Here are all the commands available:",
        color=discord.Color.darker_gray()
    )
    embed.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)
    embed.set_thumbnail(url=bot.user.avatar.url)
  
    # General Commands
    embed.add_field(
        name="__**General Commands**__",
        value="Commands that can be used by anyone.",
        inline=False
    )
    embed.add_field(name="Command", value="!botinfo", inline=True)
    embed.add_field(
        name="Description",
        value="Displays information about this bot, such as ping and total members.",
        inline=True
    )
    embed.add_field(name="Usage", value="`!botinfo`", inline=True)
  
    # Purge command
    embed.add_field(name="Command", value="!purge", inline=True)
    embed.add_field(
        name="Description",
        value="Deletes a specified number of messages. (Note: You need 'manage messages' permission to use this command)",
        inline=True
    )
    embed.add_field(name="Usage", value="`!purge <number>`", inline=True)

    # Waifu Related Commands
    embed.add_field(
        name="__**Waifu Related Commands**__",
        value="Commands related to waifu API.",
        inline=False
    )
    embed.add_field(name="Command", value="!waifu", inline=True)
    embed.add_field(
        name="Description",
        value="Gets a random image of a 'waifu'. (waifu.pics api)",
        inline=True
    )
    embed.add_field(name="Usage", value="Type `!waifu` in any channel", inline=True)
  
    # NSFW/SFW Commands
    embed.add_field(name="Command", value="!sfw", inline=True)
    embed.add_field(
        name="Description",
        value="Switches the bot to SFW mode. (waifu.pics api)",
        inline=True
    )
    embed.add_field(
        name="Usage",
        value="Type `!sfw` in any channel to switch the waifu command to SFW mode (default sfw).",
        inline=True
    )
  
    embed.add_field(name="Command", value="!nsfw", inline=True)
    embed.add_field(
        name="Description",
        value="Switches the bot to NSFW mode. (waifu.pics api)",
        inline=True
    )
    embed.add_field(
        name="Usage",
        value="Type `!nsfw` in any channel to switch the waifu command to NSFW mode.",
        inline=True
    )

    # Image Related Commands
    embed.add_field(
        name="__**AI features**__",
        value="Commands related to AI.",
        inline=False
    )
    embed.add_field(name="Command", value="!generate", inline=True)
    embed.add_field(
        name="Description",
        value="Generates 2 images based on the provided input.(Note: Please explain the input in a minimal of 5 words or more. Or will result in an error!/blank image)",
        inline=True
    )
    embed.add_field(name="Usage", value="Type `!generate <input>` in any channel", inline=True)

    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    finally:
        if session:
            asyncio.run(cleanup())