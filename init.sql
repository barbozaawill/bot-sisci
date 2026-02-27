CREATE TABLE IF NOT EXISTS suporte_interno (
    id               SERIAL      PRIMARY KEY,
    codigo_cliente   INTEGER     NOT NULL,
    contato          TEXT        NOT NULL,
    email            TEXT        NOT NULL,
    assunto          TEXT        NOT NULL,
    setor            TEXT        NOT NULL DEFAULT 'Não informado',
    assunto2         TEXT        NOT NULL,
    participantes    TEXT        NOT NULL,
    thread_id        BIGINT      NOT NULL,
    data_criacao     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    data_fechamento  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- Índice para buscas por thread_id (já usadas no /buscar)
CREATE INDEX IF NOT EXISTS idx_thread_id ON suporte_interno (thread_id);

-- Índice para buscas por setor (pra a API futura)
CREATE INDEX IF NOT EXISTS idx_setor ON suporte_interno (setor);

-- Índice para buscas por cliente
CREATE INDEX IF NOT EXISTS idx_codigo_cliente ON suporte_interno (codigo_cliente);