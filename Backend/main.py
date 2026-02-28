import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pathlib import Path

parent_dir = Path(__file__).parent.parent
load_dotenv(parent_dir / ".env")

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

COGS = [
    "Backend.topico",
    "Backend.fim",
    "Backend.buscar",
    "Backend.start_scan",
    "Backend.scan_tasks",
]

class SuporteBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("setup_hook executando")

        for cog in COGS: 
            try:
                await self.load_extension(cog)
                print(f"Cog carregado: {cog}")
            except Exception as e:
                print(f"Erro ao carregar {cog}: {e}")

        try:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild) 
            synced = await self.tree.sync()
            print(f"sync feito. {len(synced)} comandos registrados de modo global")
        except Exception as e:
            print(f"erro ao sincronizar comandos {e}")

           

    async def on_ready(self):
        print(f"🤖 Bot {self.user} ligado com sucesso.")

bot = SuporteBot()
bot.run(TOKEN)


