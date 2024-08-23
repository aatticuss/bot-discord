import discord
import random
from discord.ext import commands
import psycopg2
import requests
from bs4 import BeautifulSoup

url = 'https://wiki.python.org.br/ExerciciosFuncoes'

with open('anterior.txt', 'r') as file:
    anterior = file.read()

# Conexão com banco de dados local com nome de questoes
conn = psycopg2.connect(
    host="localhost",
    database="questoes",
    user="postgres",
    password="postgres"
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

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
    
def def_questao_diaria(anterior):
    global index
    index = random.randint(0, len(questoesBD))
    while (int(anterior) == index):
        index = random.randint(0, len(questoesBD))
    with open('anterior.txt', 'w') as arquivo:
        arquivo.write(f"{index}")
    anterior = index
    return index

index = def_questao_diaria(anterior)

@bot.event
async def on_ready():
    print(f'Me chamo bot {bot.user}')

@bot.command()
async def oi(ctx):
    await ctx.send(f"Oi, {ctx.author.mention}, tudo bem?")

@bot.command()
async def reroll(ctx):
    def_questao_diaria(anterior)
    await ctx.send(f"{ctx.author.mention} questão trocada.")

with open('file.txt', 'r') as file:
    token = file.read()

bot.run(token)