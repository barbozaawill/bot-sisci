import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os 
from db import db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


class SuporteInterno(discord.Client):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            intents=intents
        )
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        await self.tree.sync()
    
    async def on_ready(self):
        print(f"O bot {self.user} foi ligado com sucesso.")

bot = SuporteInterno()

@bot.tree.command(name="topico", description="Cria um novo tópico de suporte")
async def topico(interaction: discord.Interaction, assunto:str, cliente: int, contato: str, email: str):
    responded = False

    # Try pra tentar responder de várias formas visando outros tipos de erros, o discord tem um tempo de 3 segundos praa respostasa em tópicos, com isso da pra aumentar em até 15 min pra que não de 404
    try:
        await interaction.response.send_message("⏳ Criando tópico de suporte...")
        responded = True
    except discord.InteractionResponded:
        responded = True
    except discord.NotFound:
        print(f"Interaction expiraada para /topico - usuário: {interaction.user.name}")
        try:
            await interaction.channel.send("⏳ Criando tópico de suporte...")
            responded = True
        except:
            print(f"Erro no comando /topico - usuário: {interaction.user.name} - Canal: {interaction.channel.name if interaction.channel else None}")
            return
    except Exception as defer_error:
        # Esse erro de defer é o 404 por falta de tempo para preencher e responder o /topico 
        print(f"Erro no defer do comando /topico: {defer_error}")
        try:
            await interaction.response.send_message("⏳ Criando tópico de suporte...")
            responded = True
        except:
            print(f"Erro no comando /topico - usuário: {interaction.user.name} - Canal: {interaction.channel.name if interaction.channel else None}")
            return
    
    try:
        # Constructo pra aajudar o envio de mensagens
        async def send_message(msg):
            if responded:
                try:
                    await interaction.followup.send(msg)
                except:
                    await interaction.channel.send(msg)
            else:
                await interaction.channel.send(msg)
        
        # Algumas validações pros campos de código de cliente, assunto e etc
        if contato.isdigit() or len(contato.strip()) < 3:
            await send_message("❌ O campo 'contato' deve conter texto válido (mínimo 3 caracteres), não apenas números!")
            return
        if len(email.strip()) < 5:
            await send_message("❌ O campo 'email' deve conter um email válido (mínimo 5 caracteres)!")
            return
        if len(assunto.strip()) < 3:
            await send_message("❌ O campo 'assunto' deve conter texto válido (mínimo 3 caracteres)!")
            return
        if "@" not in email or "." not in email or email.count("@") != 1:
            await send_message("❌ Por favor, insira um e-mail válido!")
            return
        
        # Aqui cria uma thread pro discord, ele não deixa o "assunto" ter mais de 100 caracteres, mas da pra reduzir a quantidade na preview do tópico para mostrar inteiro dentro dele (meio que burlando a regra)
        if len(assunto) > 90:
            thread_name = f"🎫 {assunto[:87]}..."
        else:
            thread_name = f"🎫 {assunto}"
        thread = await interaction.channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.public_thread,
            reason=f"Tópico criado por: {interaction.user.name}"
        )

    except  Exception as e:
        print(f"Erro no comando topico: {e}")
        try:
            # Como ta sendo usendo defer lá em cima, precisa ser usado followup pois se não o discord não entende como sendo uma mensagem nova e buga
            await interaction.followup.send("❌ Ocorreu um erro ao processar o comando. Tente novamente.")
        except Exception as followup_error:
            print(f"Erro no followup: {followup_error}")
            try:
                await interaction.channel.send("❌ Erro interno do bot. Tente novamente.")
            except:
                pass

@bot.tree.command(name="fim", description="Finaliza o tópico de suporte e salva no banco de dados")
async def fim(interaction: discord.Interaction):
    #Aqui o bot vai verificar se ele está num tópico antes de finalizar ecomeçar a gravar as mensagens e etc
    if not isinstance(interaction.channel, discord.Thread):
        try:
            await interaction.response.send_message("❌ Este comando só pode ser usado dentro de um tópico de suporte!")
        except:
            try:
                await interaction.channel.send("❌ Este comando só pode ser usado dentro de um tópico de suporte!")
            except: 
                pass
        return
    
    responded = False

    # Try pra tentar responder de várias formas dependendo do contexto
    try:
        await interaction.response.send_message("⏳ Finalizando tópico e salvando no banco...")
        responded = True
    except discord.InteractionResponded:
        responded = True
    except discord.NotFound:
        print(f"Interaction expirada para /fim - usuário {interaction.user.name}")
        try:
            await interaction.channel.send("⏳ Finalizando tópico e salvando no banco...")
            responded = True
        except:
            print(f"Erro no comando /fim - usuário: {interaction.user.name} - Canal: {interaction.channel.name if interaction.channel else None}")
            return
    except Exception as defer_error:
        print(f"Erro no defer do comando /fim: {defer_error}")
        try:
            await interaction.response.send_message("⏳ Finalizando tópico e salvando no banco...")
            responded = True
        except:
            print(f"Erro no comando /fim - usuário: {interaction.user.name} - Canal: {interaction.channel.name if interaction.channel else None}")
            return
        
    try:
        thread = interaction.channel

        # Construtor pra enviar as mensagens
        async def send_message(msg):
            if responded:
                try:
                    await interaction.followup.send(msg)
                except:
                    await thread.send(msg)
            else:
                await thread.send(msg)
        
        # Coletando toda a conversa do tópico...
        mensagens = []
        async for message in thread.history(limit=None):
            if not message.author.bot: # Ignorando oq o bot escreve dentro do tópico
                timestamp = message.created_at.strftime("%d%m%Y %H %M")
                mensagens.append(f"{[timestamp]} {message.author.name}:{message.content}")

        mensagens.reverse()
        assunto2 = "\n".join(mensagens)

        participantes = []
        async for message in thread.history(limit=None):
            if not message.author.bot:
                user = message.author
                cargos = [role.name for role in user.roles if role.name != "@everyone"]
                participantes[user.name] = {
                    "nome": user.name,
                    "cargos": cargos,
                    "id": user.id
                }

        codigo_cliente = 0
        contato = "Não informado"
        email = "Não informado"
        assunto = thread.name.replace("🎫 ", "") 

        # Vai buscaar a primeiraa mensagem do bot que é o EMBED com as informações que vão ser salvas no banco
        async for message in thread.history(limite=None, oldest_first=True):
            if message.author.bot and message.embeds:
                embed = message.embeds[0]
                if embed.title == "🎫 Novo Suporte Interno":
                    for field in embed.fields:
                            if field.name == "👤 Cliente ID":
                                try:
                                    codigo_cliente = int(field.value)
                                except ValueError:
                                    codigo_cliente = 0
                            elif field.name == "📞 Contato":
                                contato = field.value
                            elif field.name == "📧 E-mail":
                                email = field.value
                            elif field.name == "📝 Assunto":
                                assunto = field.value
                    break

        # Salvar as informações recém pegas no banco
        sucesso = db.salvar_suporte(
            codigo_cliente=codigo_cliente,
            contato=contato,
            email=email,
            assunto=assunto,
            assunto2=assunto2,
            participantes=list(participantes.values()),
            thread_id=thread.id
        )

        if sucesso:
            await send_message(
                f"✅ **Tópico finalizado com sucesso!**\n"
                f"📊 **Dados salvos:**\n"
                f"• Cliente ID: {codigo_cliente}\n"
                f"• Contato: {contato}\n"
                f"• Email: {email}\n"
                f"• Assunto: {assunto}\n"
                f"• Mensagens coletadas: {len(mensagens)}\n"
                f"• Participantes: {len(participantes)}\n"
                f"• Thread ID: {thread.id}\n\n"
                f"🔒 O tópico será arquivado em alguns segundos..."
            )

            import asyncio
            await asyncio.sleep(5)
            await thread.edit(archived=True, locked=True)

        else:
            await send_message("❌ Erro ao salvar no banco de dados. Tente novamente.")
    
    except Exception as e: 
        print(f"Erro no comando fim: {e}")
        try:
            if responded:
                await interaction.followup.send("❌ Ocorreu um erro ao processar o comando. Tente novamente.")
            else:
                await interaction.channel.send("❌ Ocorreu um erro ao processar o comando. Tente novamente.")
        except Exception as send_error:
            print(f"Erro ao enviar a mensagem de erro no /fim: {send_error}")
             
bot.run(TOKEN)