import json
import discord
from discord import app_commands
from discord.ext import commands
from Backend.db import db

PREVIEW_LIMITE = 500


def _montar_preview(mensagens: list) -> str:
    conversa = "\n".join(  # FIX: era "/n" (barra normal) — não criava quebra de linha
        f"[{row[3].strftime('%d/%m/%Y %H:%M')}] {row[0]}: {row[2]}"
        for row in mensagens
    )
    return conversa[:PREVIEW_LIMITE] + "..." if len(conversa) > PREVIEW_LIMITE else conversa


class BuscarCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="buscar", description="Busca um tópico de suporte por ID de thread")
    @app_commands.describe(thread_id="ID da thread do Discord")
    async def buscar(self, interaction: discord.Interaction, thread_id: str):
        try:
            thread_id_int = int(thread_id)
        except ValueError:
            await interaction.response.send_message("ID inválido.", ephemeral=True)
            return

        await interaction.response.defer()  # FIX: defer() é mais adequado para operações lentas

        suporte = db.buscar_suporte_por_thread(thread_id_int)
        if not suporte:
            await interaction.followup.send("Nenhum suporte encontrado com esse ID.")
            return

        id_s, codigo, contato, email, assunto, setor, _, participante_json, _, data_criacao, data_fechamento = suporte
        data_criacao = data_criacao[0] if isinstance(data_criacao, tuple) else data_criacao
        data_fechamento = data_fechamento[0] if isinstance(data_fechamento, tuple) else data_fechamento
        participantes = json.loads(participante_json) if isinstance(participante_json, str) else []
        nomes = ", ".join(p["nome"] for p in participantes)

        mensagens = db.buscar_mensagens_por_thread(thread_id_int)
        mensagens = list(mensagens) if mensagens else []
        preview = _montar_preview(mensagens) if mensagens else "Sem mensagens registradas."

        embed = discord.Embed(title=f"Suporte #{id_s}", color=0x00FF00)
        embed.add_field(name="Cliente ID",    value=str(codigo),                                inline=True)
        embed.add_field(name="Contato",       value=contato,                                    inline=True)
        embed.add_field(name="Email",         value=email,                                      inline=True)
        embed.add_field(name="Setor",         value=setor,                                      inline=True)
        embed.add_field(name="Assunto",       value=assunto,                                    inline=False)
        embed.add_field(name="Participantes", value=nomes or "Não registrados",                 inline=False)
        embed.add_field(name="Aberto em",     value=data_criacao.strftime("%d/%m/%Y %H:%M"),    inline=True)
        embed.add_field(name="Fechado em",    value=data_fechamento.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="Conversa (Preview)", value=f"```{preview}```",                    inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BuscarCog(bot))