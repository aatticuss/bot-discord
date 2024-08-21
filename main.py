import os
import discord
import asyncio
import psycopg2

# Conexão com banco de dados local com nome de questoes
conn = psycopg2.connect(
    host="localhost",
    database="questoes",
    user="postgres",
    password="postgres"
)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

cur = conn.cursor()

cur.execute('SELECT * FROM questoes_diarias;')

questoes = cur.fetchall()

print(questoes)

@client.event
async def on_ready():
    print(f'Me chamo bot {client.user}')
    await asyncio.sleep(600)
    # Aqui ele printa no console o user e dps de 10 minutos (sleep 600s) ele faz algo que seria postar o desafio

    
@client.event
async def on_message(message):
    # Aqui ele checa se a msg foi dele, se for ele so volta, se n for dele e a msg for hello, ele da hello d volta
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

# client.run('your token here')