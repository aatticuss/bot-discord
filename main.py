import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

client = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Me chamo bot {client.user}')
    # await asyncio.sleep(600)

@bot.command()
async def oi(ctx):
    await ctx.send(f"Oi, {ctx.author.mention}, tudo bem?")

with open('file', 'r') as file:
    token = file.read()

bot.run('token')