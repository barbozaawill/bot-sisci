# Bot Sisci

Bot Discord para gerenciar suporte interno com PostgreSQL.

## O que faz

- Cria tópicos de suporte com `/topico`
- Finaliza e salva conversas com `/fim` 
- Busca suportes antigos com `/buscar`
- Salva tudo no PostgreSQL automaticamente

## Como usar

### Configuração inicial

1. Crie o arquivo `.env` com seu token:
```
DISCORD_TOKEN=seu_token_aqui
```

2. Suba os containers:
```bash
docker-compose up -d
```

3. Pronto! O bot já está funcionando.

### Comandos disponíveis

**`/topico`** - Cria novo suporte
- Preencha: assunto, cliente (ID), contato, email
- Cria uma thread automaticamente

**`/fim`** - Finaliza o suporte atual
- Salva toda a conversa no banco
- Arquiva a thread

**`/buscar`** - Encontra suporte antigo
- Use o ID da thread do Discord

## Banco de dados

**Configuração:**
- PostgreSQL rodando em container Docker
- Dados persistidos em volume Docker
- Configurações no arquivo `.env`

**Tabela principal:** `suporte_interno`
- Salva dados do cliente, conversa completa e participantes
- Indexada por thread_id para busca rápida

## Arquivos importantes

```
Backend/main.py     # Código do bot
Backend/db.py       # Conexão PostgreSQL  
docker-compose.yml  # Configuração dos containers
init.sql           # Cria tabelas automaticamente
```

## Comandos úteis

```bash
# Ver logs do bot
docker-compose logs -f bot

# Ver logs do banco
docker-compose logs -f postgres

# Parar tudo
docker-compose down

# Resetar banco (CUIDADO: apaga dados)
docker-compose down -v
```

## Problemas comuns

**Bot não responde:** Verifique o token no `.env`

**Erro de banco:** Confirme se PostgreSQL subiu com `docker-compose ps`

**Timeout nos comandos:** Já otimizado, mas se persistir verifique logs

## Desenvolvimento local

1. Instale PostgreSQL
2. `pip install -r requirements.txt`
3. Configure variáveis de ambiente
4. `python Backend/main.py`
