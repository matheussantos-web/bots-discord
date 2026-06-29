import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from keep_alive import keep_alive

# Carrega as senhas do arquivo .env
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'🔥 Sistema Mestre online! Operando como {bot.user}.')
    
    # Carrega todos os arquivos .py dentro da pasta "cogs"
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"📦 Módulo carregado: {filename}")
            except Exception as e:
                print(f"❌ Erro ao carregar {filename}: {e}")

keep_alive() 
bot.run(os.getenv('TOKEN_DO_BOT'))