import json
import discord
from discord import app_commands
from db import db


async def setup(bot: discord.Client):
    @bot.tree.command(name="buscar", description="Busca um suporte específico pelo ID da thread")
    @app_commands.describe(thread_id="ID da thread do Discord")
    async def buscar(interaction: discord.Interaction, thread_id: str):
        try:
            thread_id_int = int(thread_id)
        except ValueError:
            await interaction.response.send_message(
                "❌ **ID do thread deve ser um número!** Exemplo: `/buscar 1428114037769638029`",
                ephemeral=True,
            )
            return

        try:
            await interaction.response.send_message("⏳ Buscando suporte...")
        except Exception as e:
            print(f"[/buscar] Erro ao responder: {e}")
            return

        try:
            suporte = db.buscar_suporte_por_thread(thread_id_int)

            if not suporte:
                await interaction.followup.send(
                    f"❌ **Nenhum suporte encontrado com Thread ID: {thread_id}**"
                )
                return

            id_suporte, codigo_cliente, contato, email, assunto, setor, assunto2, participantes_json, thread_id_db, data_criacao, data_fechamento = suporte

            participantes = json.loads(participantes_json)

            embed = discord.Embed(
                title=f"🎫 Suporte #{id_suporte}",
                color=0x00FF00,
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="👤 Cliente ID",  value=str(codigo_cliente), inline=True)
            embed.add_field(name="📞 Contato",     value=contato,             inline=True)
            embed.add_field(name="📧 Email",       value=email,               inline=True)
            embed.add_field(name="🏢 Setor",       value=setor,               inline=True)
            embed.add_field(name="📝 Assunto",     value=assunto,             inline=False)
            embed.add_field(name="🆔 Thread ID",   value=str(thread_id_db),   inline=True)
            embed.add_field(name="📅 Fechado em",  value=str(data_fechamento),inline=True)

            participantes_texto = "\n".join(
                f"• **{p['nome']}** - {', '.join(p['cargos']) if p['cargos'] else 'Sem cargos'}"
                for p in participantes
            )
            embed.add_field(name="👥 Participantes", value=participantes_texto or "Nenhum", inline=False)

            preview = assunto2[:500] + "..." if len(assunto2) > 500 else assunto2
            embed.add_field(name="💬 Conversa (Preview)", value=f"```{preview}```", inline=False)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"[/buscar] Erro: {e}")
            await interaction.followup.send("❌ Erro ao buscar suporte.")