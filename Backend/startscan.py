import discord
from discord import app_commands
from discord.ext import commands
from Backend.db import db

class StartScanCog(commands.Cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot