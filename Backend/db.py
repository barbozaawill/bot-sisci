import psycopg2
import json
import os
from contextlib import contextmanager


class DatabaseManager:
    def __init__(self):
        self.host       = os.getenv("DB_HOST", "postgres")
        self.port       = os.getenv("DB_PORT", "5432")
        self.database   = os.getenv("DB_NAME", "botsisci")
        self.user       = os.getenv("DB_USER", "postgres")
        self.password   = os.getenv("DB_PASSWORD", "postgres123")
        self.init_database() 

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(
            host=self.host, port=self.port,
            database=self.database, user=self.user, password=self.password,
        )
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = (), fetch: str | None = None):
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()

                if fetch == "one":  return cursor.fetchone()
                if fetch == "all":  return cursor.fetchall()

    def init_database(self):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:  
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS suporte_interno (
                            id               SERIAL PRIMARY KEY,
                            codigo_cliente   INTEGER NOT NULL,
                            contato          TEXT NOT NULL,
                            email            TEXT NOT NULL,
                            assunto          TEXT NOT NULL,
                            setor            TEXT NOT NULL DEFAULT 'Não informado',
                            assunto2         TEXT NOT NULL,
                            participantes    TEXT NOT NULL,
                            thread_id        BIGINT NOT NULL,
                            data_criacao     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                            data_fechamento  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS base_conhecimento (
                            id                   SERIAL PRIMARY KEY,
                            thread_id            BIGINT NOT NULL UNIQUE,
                            titulo               TEXT NOT NULL,
                            data_criacao_topico  TIMESTAMPTZ,
                            data_scan            TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                            data_update          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                            lido_passado         BOOLEAN DEFAULT FALSE
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS mensagens (
                            id          SERIAL PRIMARY KEY,
                            thread_id   BIGINT NOT NULL,
                            message_id  BIGINT NOT NULL UNIQUE,
                            referencia_id BIGINT,
                            autor       TEXT NOT NULL,
                            conteudo    TEXT NOT NULL,
                            timestamp   TIMESTAMPTZ NOT NULL,
                            origem      TEXT NOT NULL DEFAULT 'passado'

                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS configuracoes (
                            guild_id        BIGINT PRIMARY KEY,
                            canal_scan_id   BIGINT,
                            canal_mensal_id BIGINT,
                            ritmo_scan      INTEGER DEFAULT 350,
                            scan_ativo      BOOLEAN DEFAULT FALSE,
                            canal_fonte_id  BIGINT
                        )
                    """)
                    for idx in [
                        "CREATE INDEX IF NOT EXISTS idx_thread_id       ON suporte_interno (thread_id)",
                        "CREATE INDEX IF NOT EXISTS idx_codigo_cliente  ON suporte_interno (codigo_cliente)",
                        "CREATE INDEX IF NOT EXISTS idx_bk_thread_id    ON base_conhecimento (thread_id)",
                        "CREATE INDEX IF NOT EXISTS idx_bk_data_update  ON base_conhecimento (data_update)",
                        "CREATE INDEX IF NOT EXISTS idx_bk_lido_passado ON base_conhecimento (lido_passado)",
                        "CREATE INDEX IF NOT EXISTS idx_msg_thread_id   ON mensagens (thread_id)",
                        "CREATE INDEX IF NOT EXISTS idx_msg_timestamp   ON mensagens (thread_id, timestamp ASC)",
                        "CREATE INDEX IF NOT EXISTS idx_msg_message_id  ON mensagens (message_id)",
                    ]:
                        cursor.execute(idx)

                    # Migração: garante a coluna em bancos já existentes
                    cursor.execute("""
                        ALTER TABLE base_conhecimento
                        ADD COLUMN IF NOT EXISTS data_criacao_topico TIMESTAMPTZ
                    """)

                    conn.commit()
        except Exception as e:
            print(f"Erro ao inicializar banco: {e}")

    def salvar_suporte(self, codigo_cliente, contato, email, assunto, setor, assunto2, participantes, thread_id):
        try:
            self.execute(
                """INSERT INTO suporte_interno
                   (codigo_cliente, contato, email, assunto, setor, assunto2, participantes, thread_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (codigo_cliente, contato, email, assunto, setor, assunto2,
                 json.dumps(participantes, ensure_ascii=False), thread_id),
            )
            return True
        except Exception as e:
            print(f"Erro ao salvar suporte: {e}")
            return False

    def buscar_suporte_por_thread(self, thread_id):
        return self.execute(
            "SELECT * FROM suporte_interno WHERE thread_id = %s", (thread_id,), fetch="one"
        )

    def buscar_mensagens_por_thread(self, thread_id):
        return self.execute(
            "SELECT autor, message_id, conteudo, timestamp FROM mensagens WHERE thread_id = %s ORDER BY timestamp ASC",
            (thread_id,), fetch="all",
        )

    def bk_salvar(self, thread_id, titulo, data_criacao_topico=None):
        self.execute(
            """INSERT INTO base_conhecimento (thread_id, titulo, data_criacao_topico)
               VALUES (%s, %s, %s) ON CONFLICT (thread_id) DO NOTHING""",
            (thread_id, titulo, data_criacao_topico),
        )

    def bk_buscar_por_thread(self, thread_id):
        return self.execute(
            "SELECT * FROM base_conhecimento WHERE thread_id = %s", (thread_id,), fetch="one"
        )

    def bk_listar_threads_ids_lidos(self):
        rows = self.execute(
            "SELECT thread_id FROM base_conhecimento WHERE lido_passado = TRUE", fetch="all"
        )
        return {row[0] for row in rows} if rows else set()

    def bk_marcar_lido_passado(self, thread_id):
        self.execute(
            "UPDATE base_conhecimento SET lido_passado = TRUE WHERE thread_id = %s", (thread_id,)
        )

    def bk_atualizar_data_update(self, thread_id):
        self.execute(
            "UPDATE base_conhecimento SET data_update = CURRENT_TIMESTAMP WHERE thread_id = %s",
            (thread_id,),
        )

    def mensagens_salvar_lote(self, mensagens: list[dict]) -> int:
        inseridas = 0
        for m in mensagens:
            query = """INSERT INTO mensagens (thread_id, message_id, autor, conteudo, timestamp, origem, referencia_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (message_id) DO NOTHING"""
            params = (m["thread_id"], m["message_id"], m["autor"], m["conteudo"], m["timestamp"], m["origem"], m.get("referencia_id"))
            try:
                self.execute(query, params)
                inseridas += 1
            except Exception as e:
                print(f"Erro ao salvar mensagem {m.get('message_id')}: {e}")
                print(f"Params: {params}")
        return inseridas

    def msg_existe(self, message_id: int) -> bool:
        return bool(self.execute(
            "SELECT 1 FROM mensagens WHERE message_id = %s", (message_id,), fetch="one"
        ))

    def msg_salvar(self, thread_id, message_id, autor, conteudo, timestamp, origem, referencia_id=None):
        try:
            self.execute(
                """INSERT INTO mensagens (thread_id, message_id, autor, conteudo, timestamp, origem, referencia_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (message_id) DO NOTHING""",
                (thread_id, message_id, autor, conteudo, timestamp, origem, referencia_id),
            )
        except Exception as e:
            print(f"Erro ao salvar mensagem: {e}")

    def config_salvar(self, guild_id, canal_scan_id, canal_fonte_id, canal_scan_mensal_id, ritmo_scan):
        self.execute(
            """INSERT INTO configuracoes (guild_id, canal_scan_id, canal_mensal_id, ritmo_scan, scan_ativo, canal_fonte_id)
               VALUES (%s, %s, %s, %s, TRUE, %s)
               ON CONFLICT (guild_id) DO UPDATE
               SET canal_scan_id = EXCLUDED.canal_scan_id,
                   canal_mensal_id = EXCLUDED.canal_mensal_id,
                   ritmo_scan = EXCLUDED.ritmo_scan,
                   scan_ativo = TRUE,
                   canal_fonte_id = EXCLUDED.canal_fonte_id""",
            (guild_id, canal_scan_id, canal_scan_mensal_id, ritmo_scan, canal_fonte_id),
        )

    def config_buscar(self, guild_id):
        return self.execute(
            "SELECT * FROM configuracoes WHERE guild_id = %s", (guild_id,), fetch="one"
        )

    def config_listar_ativos(self):
        return self.execute(
            "SELECT * FROM configuracoes WHERE scan_ativo = TRUE", fetch="all"
        ) or []

    def config_set_ativo(self, guild_id, ativo: bool):
        self.execute(
            "UPDATE configuracoes SET scan_ativo = %s WHERE guild_id = %s", (ativo, guild_id)
        )


db = DatabaseManager()