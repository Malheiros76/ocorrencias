import sqlite3
import hashlib

def conectar():
    return sqlite3.connect("ocorrencias.db", check_same_thread=False)

def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            setor TEXT NOT NULL
        )
    """)

    # Tabela de alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            telefone TEXT
        )
    """)

    # Tabela de ocorrências
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT NOT NULL,
            nome TEXT,
            telefone TEXT,
            data TEXT,
            descricao TEXT
        )
    """)

    # Criar usuário admin padrão, caso ainda não exista
    senha_admin = hashlib.sha256("admin".encode()).hexdigest()
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO usuarios (nome, usuario, senha, setor)
            VALUES ('Administrador', 'admin', ?, 'Administração')
        """, (senha_admin,))
        print("Usuário admin criado (usuário: admin | senha: admin)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    criar_banco()
    print("Banco de dados criado e pronto para uso.")
