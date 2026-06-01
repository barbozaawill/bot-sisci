-- =============================================================
--  bot si-sci — init.sql
--  Executado automaticamente pelo PostgreSQL na primeira vez
--  que o container sobe (docker-entrypoint-initdb.d)
-- =============================================================

-- Tabela principal de suportes finalizados
CREATE TABLE IF NOT EXISTS suporte_interno (
    id               SERIAL PRIMARY KEY,
    codigo_cliente   INTEGER NOT NULL,
    contato          TEXT NOT NULL,
    email            TEXT NOT NULL,
    assunto          TEXT NOT NULL,
    setor            TEXT NOT NULL DEFAULT 'Não informado',
    assunto2         TEXT NOT NULL,           -- Conversa completa em texto
    participantes    TEXT NOT NULL,           -- JSON com lista de participantes
    thread_id        BIGINT NOT NULL,
    data_criacao     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_fechamento  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Registro de threads já escaneadas
CREATE TABLE IF NOT EXISTS base_conhecimento (
    id            SERIAL PRIMARY KEY,
    thread_id     BIGINT NOT NULL UNIQUE,     -- Garante sem duplicatas
    titulo        TEXT NOT NULL,
    data_scan     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_update   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lido_passado  BOOLEAN DEFAULT FALSE       -- Se o ponteiro passado já processou
);

-- Mensagens individuais coletadas das threads
CREATE TABLE IF NOT EXISTS mensagens (
    id          SERIAL PRIMARY KEY,
    thread_id   BIGINT NOT NULL,
    message_id  BIGINT NOT NULL UNIQUE,             -- ID único da mensagem no Discord
    autor       TEXT NOT NULL,
    conteudo    TEXT NOT NULL,
    timestamp   TIMESTAMP NOT NULL,
    origem      TEXT NOT NULL DEFAULT 'passado',     -- 'passado' ou 'futuro'
    referencia_id BIGINT                            -- ID da mensagem referenciada (se houver)
);

-- Configurações por servidor Discord
CREATE TABLE IF NOT EXISTS configuracoes (
    guild_id        BIGINT PRIMARY KEY,
    canal_scan_id   BIGINT,                   -- Canal de logs do scan
    canal_mensal_id BIGINT,                   -- Canal para relatórios
    ritmo_scan      INTEGER DEFAULT 350,      -- Threads por rodada do ponteiro passado
    scan_ativo      BOOLEAN DEFAULT FALSE,
    canal_fonte_id  BIGINT                    -- Canal cujas threads são escaneadas
);

CREATE INDEX IF NOT EXISTS idx_thread_id        ON suporte_interno (thread_id);
CREATE INDEX IF NOT EXISTS idx_codigo_cliente   ON suporte_interno (codigo_cliente);

CREATE INDEX IF NOT EXISTS idx_bk_thread_id     ON base_conhecimento (thread_id);
CREATE INDEX IF NOT EXISTS idx_bk_data_update   ON base_conhecimento (data_update);
CREATE INDEX IF NOT EXISTS idx_bk_lido_passado  ON base_conhecimento (lido_passado);

CREATE INDEX IF NOT EXISTS idx_msg_thread_id    ON mensagens (thread_id);
CREATE INDEX IF NOT EXISTS idx_msg_timestamp    ON mensagens (thread_id, timestamp ASC);
CREATE INDEX IF NOT EXISTS idx_msg_message_id   ON mensagens (message_id);