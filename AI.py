import discord
from discord.ext import commands
import requests
import asyncio
import threading
import cachetools
import aiohttp
import time
from typing import Dict
from aiohttp import TCPConnector

# Constants
discord_token = 'MTMyNjU3MjM3MDMzMjM1NjY3OA.G7KkKj.RYUoMoaqPnNMdWToYMAwz0sicHp513KkG3YhVA'
api_key = 'pk-gwdugmthGjueuvKCRIntBnNJYALFRpvyZxBjadVUNBnfJiOf'
api_url = 'https://api.pawan.krd/cosmosrp/v1/chat/completions'
PROXY_URL = "http://159.65.170.68:80"  # Example from spys.one - replace as needed

# Initialize bot
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Optimization additions
message_cache = cachetools.TTLCache(maxsize=1000, ttl=3600)
last_response_time: Dict[int, float] = {}
RATE_LIMIT = 0.5
session = None

# Store user conversation histories
user_conversations = {}

SYSTEM_PROMPTS = [
    {'role': 'system', 'content': 'you are maddies cute girlfriend. respond in 1-2 short sentences max. use lowercase, make occasional typos, use <3 and :3 type emotes. be casual and flirty. dont use asterisks or roleplay actions. talk like a real person texting their lover.'},
    {'role': 'system', 'content': 'keep responses simple like "hiii babe <3" or "missed u sm :3" or "ur so cute when ur silly~". use casual lowercase typing with slight mistakes. be a loving girlfriend, not an AI. no explanations or formality., also youre not going to say expressions out loud, and your name is kaiya.'}
]

async def initialize_session():
    global session
    connector = TCPConnector(
        ssl=False,
        force_close=True
    )
    session = aiohttp.ClientSession(
        connector=connector,
        trust_env=True,
        headers={'HTTPS': PROXY_URL}  # Configure proxy via headers
    )

async def get_response(user_id: int, message: str) -> str:
    cache_key = f"{user_id}:{message}"
    if cache_key in message_cache:
        return message_cache[cache_key]

    current_time = time.time()
    if user_id in last_response_time:
        time_diff = current_time - last_response_time[user_id]
        if time_diff < RATE_LIMIT:
            await asyncio.sleep(RATE_LIMIT - time_diff)
    
    async with session.post(api_url, 
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'messages': user_conversations[user_id] + [{'role': 'user', 'content': message}],
            'model': 'claude-v2',
            'max_tokens': 100
        }) as response:
        
        result = await response.json()
        response_text = result['choices'][0]['message']['content']
        
        message_cache[cache_key] = response_text
        last_response_time[user_id] = time.time()
        return response_text

@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready!")
    await initialize_session()
    threading.Thread(target=terminal_input_loop, daemon=True).start()

@bot.event
async def on_message(message):
    print(f"{message.author}: {message.content}")
    await bot.process_commands(message)

    # Check if message is from bot
    if message.author == bot.user:
        return

    # Check if message is in DMs or correct channel
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_waifu_channel = getattr(message.channel, 'name', '') == 'chat-with-waifu'
    
    if not (is_dm or is_waifu_channel):
        return

    if message.author.id not in user_conversations:
        user_conversations[message.author.id] = SYSTEM_PROMPTS.copy()

    async with message.channel.typing():
        temp_msg = await message.channel.send("waifu is typing...")
        response = await get_response(message.author.id, message.content)
        await temp_msg.delete()
        await message.channel.send(response)
        user_conversations[message.author.id].append({'role': 'user', 'content': message.content})

@bot.event
async def on_message_edit(before, after):
    print(f"Edited message by {before.author}: {before.content} -> {after.content}")

async def send_message(channel_id, content):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(content)
    else:
        print("Channel not found")

def terminal_input_loop():
    while True:
        channel_id = input("Enter channel ID: ")
        message = input("Enter message to send: ")
        asyncio.run_coroutine_threadsafe(send_message(int(channel_id), message), bot.loop)

# Cleanup session on exit
@bot.event
async def on_close():
    if session:
        await session.close()
        if session.connector:
            await session.connector.close()

bot.run(discord_token)