import discord
from discord import app_commands
from discord.ext import commands
from Backend.db import db
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from Backend.scantasks import ScanTasks


class StartScanCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _scan_cog(self) -> "ScanTasks | None":
        return cast("ScanTasks | None", self.bot.get_cog("ScanTasks"))

    def _carregar_canais(self, config, guild: discord.Guild):
        guild_id, canal_scan_id, canal_mensal_id, ritmo, scan_ativo, canal_fonte_id = config
        canal_log   = guild.get_channel(canal_scan_id)
        canal_fonte = guild.get_channel(canal_fonte_id)
        return canal_log, canal_fonte, ritmo 

    async def _validar_config(self, interaction: discord.Interaction):
        config = db.config_buscar(interaction.guild_id) 
        if not config:
            await interaction.response.send_message(
                "Configuração não encontrada para este servidor. Use /start-scan para configurar.",
                ephemeral=True,
            )
            return None
        return config

    @app_commands.command(name="start-scan", description="Configura e ativa o scan automático")
    @app_commands.describe(
        canal_scan="Canal de logs do scan",
        canal_fonte="Canal de onde os scans serão feitos",
        ritmo="Tópicos por rodada (padrão: 350)",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def start_scan(
        self,
        interaction: discord.Interaction,
        canal_scan: discord.TextChannel,
        canal_fonte: discord.TextChannel,
        ritmo: int = 350,
    ):
        await interaction.response.send_message("Configurando scan...")
        db.config_salvar(
            guild_id=interaction.guild_id,
            canal_scan_id=canal_scan.id,
            canal_fonte_id=canal_fonte.id,
            canal_scan_mensal_id=canal_scan.id,
            ritmo_scan=ritmo,
        )
        embed = discord.Embed(title="✅ Scan configurado e ativado!", color=0x00FF00)
        embed.add_field(name="Canal de log",     value=canal_scan.mention)
        embed.add_field(name="Canal fonte",      value=canal_fonte.mention)
        embed.add_field(name="Ritmo por rodada", value=str(ritmo))
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="stop-scan", description="Desativa o scan automático")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def stop_scan(self, interaction: discord.Interaction):
        config = db.config_buscar(interaction.guild_id) 
        if not config or not config[4]:
            await interaction.response.send_message(
                "O scan já está desativado ou não foi configurado.", ephemeral=True
            )
            return
        db.config_set_ativo(interaction.guild_id, False)
        await interaction.response.send_message(
            "Scan pausado. Use /start-scan para reativar.", ephemeral=True
        )

    @app_commands.command(name="startp", description="Inicia manualmente o ponteiro passado")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def startp(self, interaction: discord.Interaction):

        if not interaction.guild:
            await interaction.response.send_message("Este comando só pode ser usado em um servidor.", ephemeral=True)
            return

        config = await self._validar_config(interaction)
        if not config:
            return
        
        canal_log, canal_fonte, ritmo = self._carregar_canais(config, interaction.guild)

        if not canal_log or not canal_fonte:
            await interaction.response.send_message(
                "Erro: Canais configurados não foram encontrados.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Iniciando scan manual em {canal_log.mention}..."
            )
        
        scan_cog = self._scan_cog()
        
        if not scan_cog:
            await interaction.followup.send("Erro: ScanTasks não está carregado.", ephemeral=True)
            return
        await scan_cog.executar_scan_passado(interaction.guild, canal_log, canal_fonte, ritmo)


async def setup(bot: commands.Bot):
    await bot.add_cog(StartScanCog(bot))