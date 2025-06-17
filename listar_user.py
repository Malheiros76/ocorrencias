import sqlite3

# Conectar ao banco
conn = sqlite3.connect('ocorrencias.db')
cursor = conn.cursor()

# Listar todos os usuários
cursor.execute("SELECT id, nome, usuario, setor FROM usuarios")
usuarios = cursor.fetchall()

# Exibir
print("Usuários cadastrados:")
for usuario in usuarios:
    print(f"ID: {usuario[0]} | Nome: {usuario[1]} | Usuário: {usuario[2]} | Setor: {usuario[3]}")

conn.close()
