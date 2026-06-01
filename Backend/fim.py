import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from Backend.db import db

async def _coletar_dados_thread(thread: discord.Thread):
    mensagens = []
    participantes = {}
    info_embed = {
        "codigo_cliente": 0,
        "contato": "Não informado",
        "email": "Não informado",
        "assunto": thread.name,
        "setor": "Não informado",
    }
    embed_encontrado = False

    async for message in thread.history(limit=None, oldest_first=True):
        if not embed_encontrado and message.author.bot and message.embeds:
            embed = message.embeds[0]
            if embed.title == "Novo suporte interno":
                embed_encontrado = True
                for field in embed.fields:
                    match field.name:
                        case "👤 Cliente ID":   info_embed["codigo_cliente"] = int(field.value) if field.value else 0
                        case "👤 Contato":      info_embed["contato"] = field.value or "Não informado"
                        case "📧 E-mail":        info_embed["email"] = field.value or "Não informado"
                        case "🏢 Setor":        info_embed["setor"] = field.value or "Não informado"
                    continue
        
        if not message.author.bot and message.content:
            timestamp = message.created_at.strftime("%d/%m/%Y %H:%M")
            mensagens.append(f"[{timestamp}] {message.author.name}: {message.content}")

            cargo = []
            if isinstance(message.author, discord.Member):
                cargo = [r.name for r in message.author.roles if r.name != "@everyone"]
            
            participantes[message.author.name] = {
                "nome": message.author.name,
                "cargo": cargo,
                "id": message.author.id,
            }

    return mensagens, participantes, info_embed

class FimCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="fim", description="Finaliza o tópico de suporte atual")

    async def fim(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Este comando só pode ser usado dentro de uma thread de suporte.", ephemeral=True)
            return
        
        await interaction.response.send_message("Finalizando tópico de suporte...")
        thread = interaction.channel

        if db.buscar_suporte_por_thread(thread.id):
            await interaction.followup.send("Este tópico já foi finalizado anteriormente.", ephemeral=True)
            return
        
        mensagens, participantes, info = await _coletar_dados_thread(thread)
        conversa = "\n".join(mensagens)

        sucesso = db.salvar_suporte(
            codigo_cliente=info["codigo_cliente"],
            contato=info["contato"],
            email=info["email"],
            assunto=info["assunto"],
            setor=info["setor"],
            assunto2=conversa,
            participantes=list(participantes.values()),
            thread_id=thread.id,
        )

        if sucesso:
            await interaction.followup.send("Tópico finalizado e salvo com sucesso!")
        else:
            await interaction.followup.send("Erro ao salvar o tópico. Verifique os logs para mais detalhes.")
            return
        
        await asyncio.sleep(5)
        await thread.edit(archived=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(FimCog(bot))