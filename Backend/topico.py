import discord
from discord import app_commands
from discord.ext import commands
from Backend.enums import Setor


class TopicoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="topico", description="Cria um novo tópico de suporte")
    @app_commands.describe(
        assunto="Assunto do suporte",
        cliente="ID do cliente",
        contato="Nome do contato",
        email="E-mail do contato",
        setor="Setor responsável pelo suporte",
    )
    async def topico(
        self,
        interaction: discord.Interaction,
        assunto: str,
        cliente: int,
        contato: str,
        email: str,
        setor: Setor,
    ):
        # --- Validações ---
        if contato.isdigit() or len(contato.strip()) < 3:
            await interaction.response.send_message(
                "❌ O campo 'contato' deve conter texto válido (mínimo 3 caracteres), não apenas números!",
                ephemeral=True,
            )
            return

        if len(assunto.strip()) < 3:
            await interaction.response.send_message(
                "❌ O campo 'assunto' deve conter texto válido (mínimo 3 caracteres)!",
                ephemeral=True,
            )
            return

        email = email.strip()
        if len(email) < 5 or "@" not in email or "." not in email or email.count("@") != 1:
            await interaction.response.send_message(
                "❌ Por favor, insira um e-mail válido!",
                ephemeral=True,
            )
            return

        # --- Resposta rápida (evita timeout de 3s do Discord) ---
        try:
            await interaction.response.send_message("⏳ Criando tópico de suporte...")
        except Exception as e:
            print(f"[/topico] Erro ao responder: {e}")
            return

        try:
            thread_name = f"🎫 {assunto[:87]}..." if len(assunto) > 90 else f"🎫 {assunto}"

            thread = await interaction.channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.public_thread,
                reason=f"Tópico criado por: {interaction.user.name}",
            )

            embed = discord.Embed(
                title="🎫 Novo Suporte Interno",
                description="Tópico de suporte criado com sucesso!",
                color=0x00FF00,
            )
            embed.add_field(name="👤 Cliente ID",   value=str(cliente),             inline=True)
            embed.add_field(name="📞 Contato",      value=contato,                  inline=True)
            embed.add_field(name="📧 E-mail",       value=email,                    inline=True)
            embed.add_field(name="🏢 Setor",        value=setor.value,              inline=True)
            embed.add_field(name="📝 Assunto",      value=assunto,                  inline=False)
            embed.add_field(name="👨‍💼 Solicitante", value=interaction.user.mention, inline=True)
            embed.add_field(
                name="📅 Data/Hora",
                value=f"<t:{int(interaction.created_at.timestamp())}:F>",
                inline=True,
            )
            embed.set_footer(text="Use /fim para finalizar este tópico")

            await thread.send(embed=embed)

        except Exception as e:
            print(f"[/topico] Erro: {e}")
            try:
                await interaction.followup.send("❌ Ocorreu um erro ao criar o tópico. Tente novamente.")
            except Exception as fe:
                print(f"[/topico] Erro no followup: {fe}")
                try:
                    await interaction.channel.send("❌ Erro interno do bot. Tente novamente.")
                except Exception:
                    pass


async def setup(bot: commands.Bot):
    await bot.add_cog(TopicoCog(bot))