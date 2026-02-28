import psycopg2
import json
import os
from contextlib import contextmanager
from datetime import datetime


class DatabaseManager:
    def __init__(self):
        self.host     = os.getenv("DB_HOST",     "postgres")
        self.port     = os.getenv("DB_PORT",     "5432")
        self.database = os.getenv("DB_NAME",     "suporte_interno")
        self.user     = os.getenv("DB_USER",     "postgres")
        self.password = os.getenv("DB_PASSWORD", "postgres")
        self.init_database()

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Tabela suporte_interno
                    cursor.execute("""
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
                        )
                    """)
                    cursor.execute("""
                        ALTER TABLE suporte_interno
                        ADD COLUMN IF NOT EXISTS setor TEXT NOT NULL DEFAULT 'Não informado'
                    """)

                    # Tabela base_conhecimento
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS base_conhecimento (
                            id           SERIAL      PRIMARY KEY,
                            thread_id    BIGINT      NOT NULL UNIQUE,
                            titulo       TEXT        NOT NULL,
                            conteudo     TEXT        NOT NULL,
                            data_scan    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
                            data_update  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Tabela configuracoes
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS configuracoes (
                            guild_id          BIGINT      PRIMARY KEY,
                            canal_scan_id     BIGINT,
                            canal_mensal_id   BIGINT,
                            ritmo_scan        INTEGER     DEFAULT 20,
                            scan_ativo        BOOLEAN     DEFAULT FALSE
                        )
                    """)

                    conn.commit()
            print("✅ Banco de dados PostgreSQL inicializado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao inicializar banco de dados: {e}")

    """suporte interno db"""

    def salvar_suporte(self, codigo_cliente, contato, email, assunto, setor, assunto2, participantes, thread_id):
        try:
            participantes_json = json.dumps(participantes, ensure_ascii=False)
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO suporte_interno
                            (codigo_cliente, contato, email, assunto, setor, assunto2, participantes, thread_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (codigo_cliente, contato, email, assunto, setor, assunto2, participantes_json, thread_id))
                    conn.commit()
            print(f"✅ Suporte salvo! Thread ID: {thread_id}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar suporte: {e}")
            return False

    def buscar_suporte_por_thread(self, thread_id):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM suporte_interno WHERE thread_id = %s", (thread_id,))
                    return cursor.fetchone()
        except Exception as e:
            print(f"❌ Erro ao buscar suporte: {e}")
            return None

    def listar_todos_suportes(self):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, codigo_cliente, contato, email, assunto, setor,
                               data_criacao, data_fechamento, thread_id
                        FROM suporte_interno
                        ORDER BY data_fechamento DESC
                    """)
                    return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erro ao listar suportes: {e}")
            return []

    """base_conhecimento db"""
    def bk_buscar_por_thread(self, thread_id: int):
        """Retorna o registro da base de conhecimento para o thread_id, ou None."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, thread_id, titulo, conteudo, data_scan, data_update FROM base_conhecimento WHERE thread_id = %s",
                        (thread_id,)
                    )
                    return cursor.fetchone()
        except Exception as e:
            print(f"❌ Erro ao buscar base_conhecimento: {e}")
            return None

    def bk_salvar(self, thread_id: int, titulo: str, conteudo: str):
        """Insere um novo registro na base de conhecimento."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO base_conhecimento (thread_id, titulo, conteudo)
                        VALUES (%s, %s, %s)
                    """, (thread_id, titulo, conteudo))
                    conn.commit()
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar base_conhecimento: {e}")
            return False

    def bk_atualizar(self, thread_id: int, conteudo: str):
        """Atualiza o conteúdo e data_update de um registro existente."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE base_conhecimento
                        SET conteudo = %s, data_update = CURRENT_TIMESTAMP
                        WHERE thread_id = %s
                    """, (conteudo, thread_id))
                    conn.commit()
            return True
        except Exception as e:
            print(f"❌ Erro ao atualizar base_conhecimento: {e}")
            return False

    def bk_listar_todos(self):
        """Lista todos os registros da base de conhecimento com data_update."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, thread_id, titulo, data_scan, data_update
                        FROM base_conhecimento
                        ORDER BY data_update DESC
                    """)
                    return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erro ao listar base_conhecimento: {e}")
            return []

    def bk_listar_thread_ids(self) -> set[int]:
        """Retorna um set com todos os thread_ids já salvos na base de conhecimento."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT thread_id FROM base_conhecimento")
                    return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            print(f"❌ Erro ao listar thread_ids: {e}")
            return set()

    """Configs"""
    def config_get(self, guild_id: int):
        """Retorna as configurações de um servidor, ou None."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM configuracoes WHERE guild_id = %s", (guild_id,))
                    return cursor.fetchone()
        except Exception as e:
            print(f"❌ Erro ao buscar configurações: {e}")
            return None

    def config_salvar(self, guild_id: int, canal_scan_id: int, canal_mensal_id: int, ritmo_scan: int = 20):
        """Insere ou atualiza as configurações de um servidor."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO configuracoes (guild_id, canal_scan_id, canal_mensal_id, ritmo_scan, scan_ativo)
                        VALUES (%s, %s, %s, %s, TRUE)
                        ON CONFLICT (guild_id) DO UPDATE SET
                            canal_scan_id   = EXCLUDED.canal_scan_id,
                            canal_mensal_id = EXCLUDED.canal_mensal_id,
                            ritmo_scan      = EXCLUDED.ritmo_scan,
                            scan_ativo      = TRUE
                    """, (guild_id, canal_scan_id, canal_mensal_id, ritmo_scan))
                    conn.commit()
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")
            return False

    def config_set_ativo(self, guild_id: int, ativo: bool):
        """Ativa ou desativa o scan para um servidor."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE configuracoes SET scan_ativo = %s WHERE guild_id = %s",
                        (ativo, guild_id)
                    )
                    conn.commit()
            return True
        except Exception as e:
            print(f"❌ Erro ao atualizar scan_ativo: {e}")
            return False

    def config_listar_ativos(self):
        """Lista todas as configurações de servidores com scan_ativo = TRUE."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM configuracoes WHERE scan_ativo = TRUE")
                    return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erro ao listar configurações ativas: {e}")
            return []


# Instância global
db = DatabaseManager()