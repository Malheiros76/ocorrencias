import sqlite3

def conectar():
    return sqlite3.connect('ocorrencias.db')

def listar_usuarios():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, usuario, setor FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()

    if usuarios:
        print("\n=== Lista de Usuários ===")
        for u in usuarios:
            print(f"ID: {u[0]} | Nome: {u[1]} | Login: {u[2]} | Setor: {u[3]}")
    else:
        print("\nNenhum usuário cadastrado.")

def incluir_usuario():
    nome = input("\nDigite o nome: ").strip()
    usuario = input("Digite o login: ").strip()
    senha = input("Digite a senha: ").strip()
    setor = input("Digite o setor: ").strip()

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nome, usuario, senha, setor) VALUES (?, ?, ?, ?)", 
                       (nome, usuario, senha, setor))
        conn.commit()
        print(f"Usuário '{usuario}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        print("Erro: Já existe um usuário com esse login.")
    conn.close()

def alterar_senha():
    usuario = input("\nDigite o login do usuário que deseja alterar a senha: ").strip()
    nova_senha = input("Digite a nova senha: ").strip()

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET senha = ? WHERE usuario = ?", (nova_senha, usuario))
    conn.commit()

    if cursor.rowcount > 0:
        print(f"Senha do usuário '{usuario}' alterada com sucesso!")
    else:
        print(f"Usuário '{usuario}' não encontrado.")
    conn.close()

def excluir_usuario():
    usuario = input("\nDigite o login do usuário que deseja excluir: ").strip()

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE usuario = ?", (usuario,))
    conn.commit()

    if cursor.rowcount > 0:
        print(f"Usuário '{usuario}' excluído com sucesso!")
    else:
        print(f"Usuário '{usuario}' não encontrado.")
    conn.close()

def menu():
    while True:
        print("\n=== Gerenciar Usuários (Terminal) ===")
        print("1 - Listar usuários")
        print("2 - Incluir novo usuário")
        print("3 - Alterar senha de usuário")
        print("4 - Excluir usuário")
        print("0 - Sair")

        opcao = input("\nEscolha uma opção: ")

        if opcao == '1':
            listar_usuarios()
        elif opcao == '2':
            incluir_usuario()
        elif opcao == '3':
            alterar_senha()
        elif opcao == '4':
            excluir_usuario()
        elif opcao == '0':
            break
        else:
            print("\nOpção inválida. Tente novamente.")

if __name__ == "__main__":
    menu()
