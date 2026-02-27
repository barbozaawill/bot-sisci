import psycopg2
import psycopg2.extras
import json
import os
from contextlib import contextmanager


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
        """Context manager para conexão — garante que sempre será fechada."""
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
        """Cria a tabela se não existir."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
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

                    # Adiciona coluna setor em bancos já existentes (migração segura)
                    cursor.execute("""
                        ALTER TABLE suporte_interno
                        ADD COLUMN IF NOT EXISTS setor TEXT NOT NULL DEFAULT 'Não informado'
                    """)

                    conn.commit()
            print("✅ Banco de dados PostgreSQL inicializado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao inicializar banco de dados: {e}")

    def salvar_suporte(self, codigo_cliente, contato, email, assunto, setor, assunto2, participantes, thread_id):
        """Salva os dados do suporte interno no banco."""
        try:
            participantes_json = json.dumps(participantes, ensure_ascii=False)

            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO suporte_interno
                            (codigo_cliente, contato, email, assunto, setor, assunto2, participantes, thread_id)
                        VALUES
                            (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (codigo_cliente, contato, email, assunto, setor, assunto2, participantes_json, thread_id))
                    conn.commit()

            print(f"✅ Suporte salvo! Thread ID: {thread_id}")
            return True

        except Exception as e:
            print(f"❌ Erro ao salvar no banco: {e}")
            return False

    def buscar_suporte_por_thread(self, thread_id):
        """Busca suporte pelo ID da thread."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM suporte_interno WHERE thread_id = %s
                    """, (thread_id,))
                    return cursor.fetchone()

        except Exception as e:
            print(f"❌ Erro ao buscar no banco: {e}")
            return None

    def listar_todos_suportes(self):
        """Lista todos os suportes salvos."""
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


# Instância global do banco
db = DatabaseManager()