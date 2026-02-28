import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from Backend.db import db


async def _coletar_dados_thread(thread: discord.Thread) -> tuple[list[str], dict, dict]:
    mensagens: list[str] = []
    participantes: dict = {}
    info_embed: dict = {
        "codigo_cliente": 0,
        "contato": "Não informado",
        "email": "Não informado",
        "assunto": thread.name.replace("🎫 ", ""),
        "setor": "Não informado",
    }
    embed_encontrado = False

    async for message in thread.history(limit=None, oldest_first=True):
        # Embed de abertura (criado pelo bot)
        if not embed_encontrado and message.author.bot and message.embeds:
            embed = message.embeds[0]
            if embed.title == "🎫 Novo Suporte Interno":
                embed_encontrado = True
                for field in embed.fields:
                    match field.name:
                        case "👤 Cliente ID":
                            try:
                                info_embed["codigo_cliente"] = int(field.value)
                            except ValueError:
                                pass
                        case "📞 Contato":
                            info_embed["contato"] = field.value
                        case "📧 E-mail":
                            info_embed["email"] = field.value
                        case "📝 Assunto":
                            info_embed["assunto"] = field.value
                        case "🏢 Setor":
                            info_embed["setor"] = field.value
            continue

        # Mensagens de usuários reais
        if not message.author.bot:
            timestamp = message.created_at.strftime("%d/%m/%Y %H:%M")
            mensagens.append(f"[{timestamp}] {message.author.name}: {message.content}")

            if message.author.name not in participantes:
                cargos = [r.name for r in message.author.roles if r.name != "@everyone"]
                participantes[message.author.name] = {
                    "nome": message.author.name,
                    "cargos": cargos,
                    "id": message.author.id,
                }

    return mensagens, participantes, info_embed


class FimCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="fim", description="Finaliza o tópico de suporte e salva no banco de dados")
    async def fim(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message(
                "❌ Este comando só pode ser usado dentro de um tópico de suporte!",
                ephemeral=True,
            )
            return

        try:
            await interaction.response.send_message("⏳ Finalizando tópico e salvando no banco...")
        except Exception as e:
            print(f"[/fim] Erro ao responder: {e}")
            return

        thread = interaction.channel

        async def send(msg: str):
            try:
                await interaction.followup.send(msg)
            except Exception:
                await thread.send(msg)

        try:
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
                await send(
                    f"✅ **Tópico finalizado com sucesso!**\n"
                    f"📊 **Dados salvos:**\n"
                    f"• Cliente ID: {info['codigo_cliente']}\n"
                    f"• Contato: {info['contato']}\n"
                    f"• Email: {info['email']}\n"
                    f"• Setor: {info['setor']}\n"
                    f"• Assunto: {info['assunto']}\n"
                    f"• Mensagens coletadas: {len(mensagens)}\n"
                    f"• Participantes: {len(participantes)}\n"
                    f"• Thread ID: {thread.id}\n\n"
                    f"🔒 O tópico será arquivado em alguns segundos..."
                )
                await asyncio.sleep(5)
                await thread.edit(archived=True, locked=True)
            else:
                await send("❌ Erro ao salvar no banco de dados. Tente novamente.")

        except Exception as e:
            print(f"[/fim] Erro: {e}")
            try:
                await interaction.followup.send("❌ Ocorreu um erro ao processar o comando. Tente novamente.")
            except Exception as fe:
                print(f"[/fim] Erro no followup: {fe}")


async def setup(bot: commands.Bot):
    await bot.add_cog(FimCog(bot))