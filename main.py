import asyncio
import discord
from discord.ext import commands
import psycopg2
import datetime
import requests
from bs4 import BeautifulSoup
import random

# Setup
url = 'https://wiki.python.org.br/ExerciciosFuncoes'

with open('anterior.txt', 'r') as file:
    anterior = file.read()

# Conexão com banco de dados
conn = psycopg2.connect(
    host="localhost",
    database="questoes",
    user="postgres",
    password="postgres"
)

try:
    cur = conn.cursor()
    cur.execute('SELECT texto FROM questoes_diarias;')
    questoesBD = cur.fetchall()
    if not questoesBD:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            questoes = soup.find_all("li", class_="gap")
            questao = [questao.get_text(strip=True, separator=" ") for questao in questoes]
            for txt in questao:
                cur.execute("INSERT INTO questoes_diarias (texto) VALUES (%s)", (txt,))
            conn.commit()
            cur.execute('SELECT texto FROM questoes_diarias;')
            questoesBD = cur.fetchall()
except Exception as e:
    print(f"Ocorreu um erro: {e}")

# Config do bot
intents = discord.Intents.default()
intents.message_content = True
chat_id = 1259632923095597100

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

def def_questao_diaria(anterior):
    global index
    index = random.randint(0, len(questoesBD)-1)
    while (int(anterior) == index):
        index = random.randint(0, len(questoesBD)-1)
    with open('anterior.txt', 'w') as arquivo:
        arquivo.write(f"{index}")
    anterior = index
    return index

index = def_questao_diaria(anterior)

async def gera_questao():
    # Define quando executar
    time = datetime.datetime.now().replace(hour=21, minute=31, second=0)
    # Pega data de agora
    agora = datetime.datetime.now()
    def_questao_diaria(anterior)
    channel = bot.get_channel(chat_id)
    if channel:
        await channel.send(questoesBD[index])
    # Empurra para o mesmo horário no proximo dia
    # time += datetime.timedelta(days = 1)
    # Espera até o horário definido
    downtime = (time - agora).total_seconds()
    await asyncio.sleep(downtime)

# Eventos
@bot.event
async def on_ready():
    print(f'Me chamo bot {bot.user}')
    channel = bot.get_channel(chat_id)
    if channel:
        await channel.send('Olá, estou online.')
    bot.loop.create_task(gera_questao())

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
# Abre uma mensagem sobre o bot
async def about(ctx):
    await ctx.send(f"Olá, me chamo {bot.user}. Minha função é gerar diariamente um desafio de programação para testar seus conhecimentos e garantir que você não fique um dia sequer sem praticar.\n\nDigite !help para checar meus comandos!")

@bot.command(name="r")
async def reroll(ctx):
# Troca a questão
    def_questao_diaria(anterior)
    await ctx.send(f"{ctx.author.mention} questão trocada.")
    bot.loop.create_task(gera_questao())

@bot.command(name="d")
async def daily(ctx):
# Repete a questão diária
    question_msg = discord.Embed(title="Desafio do dia", description=None, color=discord.Color.darker_grey())
    question_msg.set_author(name = ctx.author.display_name, icon_url=ctx.author.avatar)
    question_msg.add_field(name="Questão", value=questoesBD[index], inline=True)
    question_msg.set_footer(text="Reaja à mensagem quando terminar.", icon_url=bot.user.avatar)
    await ctx.send(embed=question_msg)

bot.run(token)    