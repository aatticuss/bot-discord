import asyncio
import os
from dotenv import load_dotenv
import discord
import random
from discord.ext import commands
import psycopg2
import datetime
import requests
from bs4 import BeautifulSoup

load_dotenv()

url = os.getenv('URL')
host = os.getenv('HOST')
database = os.getenv('DATABASE')
user = os.getenv('USER')
password = os.getenv('PASSWORD')
chat_id = int(os.getenv('CHAT_ID'))
token = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

# Conexão com banco de dados local com nome de questoes
conn = psycopg2.connect(
    host=host,
    database=database,
    user=user,
    password=password
)

def query_questoesBD():
    try:
        cur = conn.cursor()
        cur.execute('SELECT texto FROM questoes_diarias;')
        global questoesBD
        questoesBD = cur.fetchall()
        if questoesBD:
            questoesBD = [questao[0] for questao in questoesBD]

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
                questoesBD = [questao[0] for questao in questoesBD]
                cur.close
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    
def def_questao_diaria():
    global index
    index = random.randint(0, len(questoesBD))
    cur = conn.cursor()
    cur.execute('SELECT valor FROM anterior;')
    anterior = cur.fetchone()
    if anterior is None:
        cur.execute('INSERT INTO anterior VALUES (%s)', (index,))
    else:
        anterior = anterior[0]
        while (anterior == index):
            index = random.randint(0, len(questoesBD))
        cur.execute('UPDATE anterior SET valor = %s WHERE id = 1', (index,))
    conn.commit()
    cur.close()
    return index

async def gera_questao():
    # Define quando executar
    time = datetime.datetime.now().replace(hour=10, minute=0, second=0)
    # Pega data de agora
    agora = datetime.datetime.now()
    downtime = (time - agora).total_seconds()
    await asyncio.sleep(downtime)
    await print_question()
    # Empurra para o mesmo horário no proximo dia
    time += datetime.timedelta(days = 1)
    # Espera até o horário definido
    downtime = (time - agora).total_seconds()
    await asyncio.sleep(downtime)
    await gera_questao()

async def print_question(author = None):
    question_msg = discord.Embed(title="Desafio do dia", description=None, color=discord.Color.darker_grey())
    if author is not None:
        question_msg.set_author(name = author)
    question_msg.add_field(name="Questão", value=questoesBD[index], inline=True)
    question_msg.set_footer(text="Reaja à mensagem quando terminar.", icon_url=bot.user.avatar)
    channel = bot.get_channel(chat_id)
    if channel:
        await channel.send(embed=question_msg)

@bot.event
async def on_ready():
    query_questoesBD()
    global index
    index = def_questao_diaria()
    await gera_questao()

@bot.command(aliases = ["ola", "eai", "oii", "oie"])
async def oi(ctx):
    await ctx.send(f"Oi, {ctx.author.mention}, tudo bem?")

@bot.command(aliases = ["h"])
async def ajuda(ctx):
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

@bot.command(aliases=["abt"])
# Abre uma mensagem sobre o bot
async def about(ctx):
    await ctx.send(f"Olá, me chamo {bot.user}. Minha função é gerar diariamente um desafio de programação para testar seus conhecimentos e garantir que você não fique um dia sequer sem praticar.\n\nDigite !help para checar meus comandos!")

@bot.command(aliases=["r"])
async def reroll(ctx):
# Troca a questão
    def_questao_diaria()
    await ctx.send(f"{ctx.author.mention} questão trocada.")
    await print_question(ctx.author.display_name)

@bot.command(aliases=["d"])
async def daily(ctx):
# Repete a questão diária
    await print_question(ctx.author.display_name)

bot.run(token)