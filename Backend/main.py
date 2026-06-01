import discord
from discord.ext import commands
import os
import traceback
from dotenv import load_dotenv
from pathlib import Path

parent_dir = Path(__file__).parent.parent
load_dotenv(parent_dir / ".env")

DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = os.getenv("GUILD_ID", "0")

COGS = [
    "Backend.topicos",
    "Backend.fim",
    "Backend.buscar",
    "Backend.startscan",
    "Backend.scantasks",
]


class SuporteBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("setuphook executando")
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"Cog carregado: {cog}")
            except Exception:
                traceback.print_exc()

        guild = discord.Object(id=int(GUILD_ID)) 
        self.tree.copy_global_to(guild=guild)

        synced = await self.tree.sync(guild=guild)
        print(f"Sync feito. {len(synced)} comandos registrados no servidor")

    async def on_ready(self):
        print(f"Bot {self.user} ligado com sucesso")


bot = SuporteBot()
bot.run(DISCORD_TOKEN)