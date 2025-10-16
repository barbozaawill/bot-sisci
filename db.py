import sqlite3
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="suporte_interno.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Cria a tabela se não existir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suporte_interno (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_cliente INTEGER NOT NULL,
                contato TEXT NOT NULL,
                email TEXT NOT NULL,
                assunto TEXT NOT NULL,
                assunto2 TEXT NOT NULL,
                participantes TEXT NOT NULL,
                thread_id INTEGER NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_fechamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    
    def salvar_suporte(self, codigo_cliente, contato, email, assunto, assunto2, participantes, thread_id):
        """Salva os dados do suporte interno no banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Converter participantes para JSON string
            participantes_json = json.dumps(participantes, ensure_ascii=False)
            
            cursor.execute('''
                INSERT INTO suporte_interno 
                (codigo_cliente, contato, email, assunto, assunto2, participantes, thread_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (codigo_cliente, contato, email, assunto, assunto2, participantes_json, thread_id))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Suporte salvo no banco! Thread ID: {thread_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar no banco: {e}")
            return False
    
    def buscar_suporte_por_thread(self, thread_id):
        """Busca dados de suporte pelo ID do thread"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM suporte_interno WHERE thread_id = ?
            ''', (thread_id,))
            
            resultado = cursor.fetchone()
            conn.close()
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro ao buscar no banco: {e}")
            return None
    
    def listar_todos_suportes(self):
        """Lista todos os suportes salvos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, codigo_cliente, contato, email, assunto, 
                       data_criacao, data_fechamento, thread_id
                FROM suporte_interno 
                ORDER BY data_fechamento DESC
            ''')
            
            resultados = cursor.fetchall()
            conn.close()
            
            return resultados
            
        except Exception as e:
            print(f"❌ Erro ao listar suportes: {e}")
            return []

# Instância global do banco
db = DatabaseManager()
