import sqlite3

conn = sqlite3.connect("ocorrencias.db")
cursor = conn.cursor()

# Corrigindo: Inserir também o campo 'usuario' (login)
cursor.execute("""
    INSERT INTO usuarios (nome, usuario, senha, setor)
    VALUES (?, ?, ?, ?)
""", ("Administrador", "admin", "admin", "Administração"))

conn.commit()
conn.close()

print("Usuário admin criado com sucesso!")
