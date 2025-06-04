import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect("ocorrencias.db")
cursor = conn.cursor()

# Criar a tabela de usuários
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    nivel_acesso TEXT NOT NULL
)
""")

# Inserir usuário administrador padrão (evita duplicação)
cursor.execute("""
INSERT OR IGNORE INTO usuarios (nome, usuario, senha, nivel_acesso)
VALUES (?, ?, ?, ?)
""", ("Administrador", "admin", "1234", "admin"))

# Salvar e fechar
conn.commit()
conn.close()

print("Tabela de usuários criada com sucesso. Usuário admin: 'admin' / senha: '1234'")
