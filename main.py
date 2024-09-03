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

#Variáveis de Ambiente
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

#Função para coleta de questões do banco de dados e armazenagem em variável global
async def query_questionsBD():
    try:
        cur = conn.cursor()
        cur.execute('SELECT texto FROM questoes_diarias;')
        global questoesBD
        questoesBD = cur.fetchall()
        if questoesBD:
            questoesBD = [questao[0] for questao in questoesBD]
        if not questoesBD:
            send("Nenhuma questão no banco de dados, tente o comando !url")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    
def def_daily_question():
    global index
    index = random.randint(0, len(questoesBD) - 1)
    cur = conn.cursor()
    cur.execute('SELECT valor FROM anterior;')
    anterior = cur.fetchone()
    if anterior is None:
        cur.execute('INSERT INTO anterior VALUES (%s)', (index,))
    else:
        anterior = anterior[0]
        while (anterior == index):
            index = random.randint(0, len(questoesBD) - 1)
        cur.execute('UPDATE anterior SET valor = %s WHERE id = 1', (index,))
    conn.commit()
    cur.close()
    return index

async def schedule_question():
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
    await schedule_question()

async def print_question(author = None):
    #Printa a questao diaria
    question_msg = discord.Embed(title="Desafio do dia", description=None, color=discord.Color.darker_grey())
    if author is not None:
        question_msg.set_author(name = author)
    question_msg.add_field(name="Questão", value=questoesBD[index], inline=True)
    question_msg.set_footer(text="Reaja à mensagem quando terminar.", icon_url=bot.user.avatar)
    await send(question_msg, True)

async def send(msg, embeder = False):
    #Envia mensagens ao canal geral, 
    #pode ser uma mensagem embed se for enviada no formato: send(msg, True)
    channel = bot.get_channel(chat_id)
    if channel:
        if embeder is True:
            await channel.send(embed=msg)
        else:
            await channel.send(msg)

async def get_source(url, html_tag, tag_class = None):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            questions = soup.find_all(html_tag, class_=tag_class)
            if not questions:
                await send('Nenhum elemento encontrado com a tag e classe fornecidas.')
                return
            else:
                cur = conn.cursor()
                questao = [questao.get_text(strip=True, separator=" ") for questao in questions]
                await send(f'Foram adicionadas {len(questao)} novas questões')
                for txt in questao:
                        cur.execute("INSERT INTO questoes_diarias (texto) VALUES (%s)", (txt,))
                conn.commit()
                cur.close()
                await query_questionsBD()
    except Exception as e:
        await send(f'Ocorreu um erro: {e}')

@bot.event
async def on_ready():
    await query_questionsBD()
    global index
    index = def_daily_question()
    #await schedule_question()

@bot.command(aliases = ['ola', 'eai', 'oii', 'oie'])
async def oi(ctx):
    await ctx.send(f"Oi, {ctx.author.mention}, tudo bem?")

@bot.command(aliases = ['ajuda'])
async def h(ctx):
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

@bot.command(aliases=['abt', 'sobre'])
# Abre uma mensagem sobre o bot
async def about(ctx):
    await ctx.send(f"Olá, me chamo {bot.user}. Minha função é gerar diariamente um desafio de programação para testar seus conhecimentos e garantir que você não fique um dia sequer sem praticar.\n\nDigite !help para checar meus comandos!")

@bot.command(aliases=['r'])
async def reroll(ctx):
# Troca a questão
    def_daily_question()
    await ctx.send(f"{ctx.author.mention} questão trocada.")
    await print_question(ctx.author.display_name)

@bot.command(aliases=['d', 'diaria'])
async def daily(ctx):
# Repete a questão diária
    await print_question(ctx.author.display_name)

@bot.command(aliases=['link', 'source'])
async def url(ctx):
    params = ctx.message.content
    params = params.split()
    if len(params) >= 4:
        url = params[1]
        tag = params[2]
        tag_class = params[3]
        if url.startswith(("http://", "https://")):
            await get_source(url, tag, tag_class)
        else:
            await send("URL inválida")
    elif len(params) == 3:
        url = params[1]
        tag = params[2]
        if url.startswith(("http://", "https://")):
            await get_source(url, tag)
        else:
            await send("URL inválida")
    elif len(params) < 3:
        await send("Argumentos insuficientes, tente !url link tag class(opcional) e garanta que seu link comece com http ou https")

@bot.command(aliases=['listar', 'perguntas'])
async def list(ctx):
    global pages
    pages = []

    current_page = discord.Embed(title="Página 1", description="Abaixo está uma lista com as questões no banco de dados do GPCão", color=discord.Color.darker_grey())
    pages.append(current_page)
    
    max_lenght = 2000
    current_lenght = len(current_page.description)
    i = 1
    for questao in questoesBD:
        questao_lenght = len(f'Pergunta {i}: {questao}')
        # Verifica se adicionar a próxima questão ultrapassará o limite
        if (current_lenght + questao_lenght) < max_lenght:
            current_page.add_field(name=f"Pergunta {i}", value=f"{questao}", inline=False)
            current_lenght += questao_lenght
        else:
            # Cria uma nova página
            current_page = discord.Embed(title=f"Página {len(pages) + 1}", description="Abaixo está uma lista com as questões no banco de dados do GPCão", color=discord.Color.darker_grey())
            pages.append(current_page)
            current_page.add_field(name=f"Pergunta {i}", value=f"{questao}", inline=False)
            current_lenght = len(current_page.description) + questao_lenght

        i += 1

    message = await ctx.send(embed=pages[0])
    await message.add_reaction('⬅️')
    await message.add_reaction('➡️')

    bot.current_message = message
    bot.current_page = 0

@bot.event
async def on_reaction_add(reaction, user):
    # Certifique-se de que a reação é do usuário correto e na mensagem correta
    if user.bot:
        return

    if reaction.message.id != bot.current_message.id:
        return

    if str(reaction.emoji) == '⬅️':
        if bot.current_page > 0:
            bot.current_page -= 1
            await bot.current_message.edit(embed=pages[bot.current_page])
    
    elif str(reaction.emoji) == '➡️':
        if bot.current_page < len(pages) - 1:
            bot.current_page += 1
            await bot.current_message.edit(embed=pages[bot.current_page])
    
    await bot.current_message.remove_reaction(reaction, user)
            
bot.run(token)