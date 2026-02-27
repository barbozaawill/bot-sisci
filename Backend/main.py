import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import os

parent_dir = Path(__file__).parent.parent
load_dotenv(parent_dir / ".env")
TOKEN = os.getenv("DISCORD_TOKEN")

COGS = [
    "cogs.topico",
    "cogs.fim",
    "cogs.buscar",
]


class SuporteInterno(discord.Client):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        for cog in COGS:
            try:
                # Importa e registra os comandos de cada cog
                module = __import__(cog, fromlist=["setup"])
                await module.setup(self)
                print(f"✅ Cog carregado: {cog}")
            except Exception as e:
                print(f"❌ Erro ao carregar cog {cog}: {e}")

        await self.tree.sync()
        print("🔄 Comandos sincronizados com o Discord.")

    async def on_ready(self):
        print(f"🤖 Bot {self.user} ligado com sucesso.")


bot = SuporteInterno()
bot.run(TOKEN)