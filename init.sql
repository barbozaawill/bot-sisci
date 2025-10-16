-- Script de inicialização do banco de dados PostgreSQL

-- Criar a tabela suporte_interno se não existir
CREATE TABLE IF NOT EXISTS suporte_interno (
    id SERIAL PRIMARY KEY,
    codigo_cliente INTEGER NOT NULL,
    contato TEXT NOT NULL,
    email TEXT NOT NULL,
    assunto TEXT NOT NULL,
    assunto2 TEXT NOT NULL,
    participantes TEXT NOT NULL,
    thread_id BIGINT NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_fechamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_suporte_thread_id ON suporte_interno(thread_id);
CREATE INDEX IF NOT EXISTS idx_suporte_codigo_cliente ON suporte_interno(codigo_cliente);
CREATE INDEX IF NOT EXISTS idx_suporte_data_fechamento ON suporte_interno(data_fechamento);

COMMENT ON TABLE suporte_interno IS 'Tabela para armazenar dados dos suportes internos do Discord';
COMMENT ON COLUMN suporte_interno.id IS 'ID único do suporte';
COMMENT ON COLUMN suporte_interno.codigo_cliente IS 'Código identificador do cliente';
COMMENT ON COLUMN suporte_interno.contato IS 'Nome do contato do cliente';
COMMENT ON COLUMN suporte_interno.email IS 'Email do cliente';
COMMENT ON COLUMN suporte_interno.assunto IS 'Assunto do suporte';
COMMENT ON COLUMN suporte_interno.assunto2 IS 'Conversa completa do suporte';
COMMENT ON COLUMN suporte_interno.participantes IS 'JSON com dados dos participantes';
COMMENT ON COLUMN suporte_interno.thread_id IS 'ID da thread do Discord';
COMMENT ON COLUMN suporte_interno.data_criacao IS 'Data de criação do registro';
COMMENT ON COLUMN suporte_interno.data_fechamento IS 'Data de fechamento do suporte';
