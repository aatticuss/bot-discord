import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

client = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Me chamo bot {bot.user}')
    # await asyncio.sleep(600)

with open('token.txt', 'r') as file:
    token = file.read()

# Comandos
@bot.command(aliases = ["ola", "eai", "oii", "oie"])
async def oi(ctx):
    await ctx.send(f"Oi, {ctx.author.mention}, tudo bem?")

@bot.command(name = "h")
async def help(ctx):
    # Abre uma mensagem embed
    help_msg = discord.Embed(title="Guia de comandos", description="Abaixo está uma lista com todos os comandos do GPCão.", color=discord.Color.darker_grey())
    help_msg.add_field(name="espaçamento", value="\u200b", inline=True)
    # fields são campos de texto
    help_msg.set_author(name = ctx.author.display_name, icon_url=ctx.author.avatar)
    help_msg.set_thumbnail(url=ctx.guild.icon)  
    help_msg.add_field(name="!oi", value="Cumprimenta o usuário.", inline=False)
    help_msg.add_field(name="!daily", value="Gera um desafio de código diário. ", inline=False)
    help_msg.add_field(name="!reroll", value="Redefine o desafio gerado. Tome cuidado, você só pode realizar essa ação 3 vezes por dia.", inline=False)
    help_msg.add_field(name="espaçamento", value="\u200b", inline=True)
    help_msg.set_footer(text="Fornecido por {}".format(bot.user), icon_url=bot.user.avatar)
    await ctx.send(embed=help_msg)

@bot.command(name="abt")
async def about(ctx):
    await ctx.send(f"Olá, me chamo {bot.user}. Minha função é gerar diariamente um desafio de programação para testar seus conhecimentos e garantir que você não fique um dia sequer sem praticar.\nDigite !help para checar meus comandos!")

bot.run(token)    