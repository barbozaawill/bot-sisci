import asyncio
from discord.ext import commands, tasks  
import discord
from datetime import datetime, timezone, timedelta
from Backend.db import db


async def _coletar_mensagens(thread: discord.Thread, origem: str) -> list[dict]:
    mensagens = []
    async for mensagem in thread.history(limit=1000, oldest_first=True):

        referencia_id = None
        if mensagem.reference:
            if mensagem.reference.message_id:
                referencia_id = mensagem.reference.message_id
            elif mensagem.reference.resolved:
                referencia_id = mensagem.reference.resolved.id

        if mensagem.author.bot:
            continue

        if mensagem.type not in (
            discord.MessageType.default,
            discord.MessageType.reply,
        ):
            continue

        conteudo = mensagem.content

        if not conteudo and mensagem.attachments:
            conteudo = "[ANEXO]"

        if not conteudo and mensagem.embeds:
            conteudo = "[EMBEDS]"

        if not conteudo:
            conteudo = "[SEM CONTEÚDO]"

        mensagens.append({
            "thread_id":  thread.id,
            "message_id": mensagem.id,
            "autor":      mensagem.author.display_name,
            "conteudo":   conteudo,
            "timestamp":  mensagem.created_at,
            "origem":     origem,
            "referencia_id": referencia_id,
        })
    return mensagens

async def _executar_ponteiro_pasado(guild, canal_log, canal_fonte, ritmo: int):

    await canal_log.send("Buscando threads pendentes...")

    thread_ids_lidos = db.bk_listar_threads_ids_lidos()

    pendentes = []

    threads_vistas = set()

    for t in canal_fonte.threads:
        if t.id not in thread_ids_lidos:
            pendentes.append(t)
            threads_vistas.add(t.id)

    async for thread in canal_fonte.archived_threads(limit=None):
        if thread.id not in thread_ids_lidos and thread.id not in threads_vistas:
            pendentes.append(thread)

    lote = pendentes[:ritmo]
    total_inseridas = 0

    await canal_log.send(
        f"Ponteiro passado iniciado\n"
        f"Threads pendentes {len(pendentes)}\n"
        f"Processando neste ciclo {len(lote)}\n"
        f"Ritmo configurado {ritmo}\n"
    )

    for thread in lote:
        try:

            await canal_log.send(f"Processando thread {thread.name}")

            mensagens = await _coletar_mensagens(thread, origem="passado")
            inseridas = db.mensagens_salvar_lote(mensagens)

            if inseridas > 0:
                db.bk_salvar(thread.id, thread.name, thread.created_at)
                db.bk_marcar_lido_passado(thread.id)

            total_inseridas += inseridas

        except Exception as e:
            await canal_log.send(f"Erro em '{thread.name}': {e}")

    await canal_log.send(f"Ponteiro passado concluído - {total_inseridas} mensagens inseridas.")


async def _registrar_mensagem_nova(mensagem: discord.Message, canal_fonte_id: int):
    if mensagem.author.bot or not mensagem.content:
        return
    if not isinstance(mensagem.channel, discord.Thread):
        return
    if mensagem.channel.parent_id != canal_fonte_id:
        return

    thread = mensagem.channel

    if not db.bk_buscar_por_thread(thread.id):
        db.bk_salvar(thread.id, thread.name, thread.created_at)

    if db.msg_existe(mensagem.id):  
        return

    referencia_id = None
    if mensagem.reference and mensagem.reference.message_id:
        referencia_id = mensagem.reference.message_id

    db.msg_salvar(
        thread_id=thread.id,
        message_id=mensagem.id,
        autor=mensagem.author.display_name,
        conteudo=mensagem.content,
        timestamp=mensagem.created_at,
        origem="futuro",
        referencia_id=referencia_id,
    )
    db.bk_atualizar_data_update(thread.id)


class ScanTasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scan_passado.start()

    async def cog_unload(self):
        self.scan_passado.cancel()

    async def _carregar_config(self, guild_id: int):
        config = db.config_buscar(guild_id)
        if not config:
            return None
        guild_id_config, canal_scan_id, canal_mensal_id, ritmo, scan_ativo, canal_fonte_id = config
        guild_id_config = int(guild_id_config[0]) if isinstance(guild_id_config, tuple) else int(guild_id_config)
        canal_scan_id = int(canal_scan_id[0]) if isinstance(canal_scan_id, tuple) else int(canal_scan_id)
        canal_fonte_id = int(canal_fonte_id[0]) if isinstance(canal_fonte_id, tuple) else int(canal_fonte_id)
        guild       = self.bot.get_guild(guild_id)
        if not guild:
            return None
        canal_log   = guild.get_channel(canal_scan_id)
        canal_fonte = guild.get_channel(canal_fonte_id)
        return guild, canal_log, canal_fonte, ritmo


    @commands.Cog.listener()
    async def on_message(self, mensagem: discord.Message):
        if mensagem.author.bot or not mensagem.guild:
            return
        for config in db.config_listar_ativos():
            guild_id, _, _, _, _, canal_fonte_id = config
            if mensagem.guild.id != guild_id: 
                continue
            await _registrar_mensagem_nova(mensagem, canal_fonte_id)

        await self.bot.process_commands(mensagem)

    @tasks.loop(hours=24) 
    async def scan_passado(self):
        for config in db.config_listar_ativos():
            dados = await self._carregar_config(config[0])  
            if dados:
                guild, canal_log, canal_fonte, ritmo = dados
                ritmo_int = int(ritmo[0]) if isinstance(ritmo, tuple) else int(ritmo)
                await _executar_ponteiro_pasado(guild, canal_log, canal_fonte, ritmo_int)

    @scan_passado.before_loop
    async def before_scan_passado(self):
        await self.bot.wait_until_ready()
        now = datetime.now(timezone.utc)
        target = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

    async def executar_scan_passado(self, guild, canal_log, canal_fonte, ritmo):
        await _executar_ponteiro_pasado(guild, canal_log, canal_fonte, ritmo)


async def setup(bot: commands.Bot):
    await bot.add_cog(ScanTasks(bot))