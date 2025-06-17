import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# Conexão com banco
def conectar():
    return sqlite3.connect("ocorrencias.db", check_same_thread=False)

# Função para verificar login
def verificar_login(usuario, senha):
    conn = conectar()
    cursor = conn.cursor()
    senha_criptografada = hashlib.sha256(senha.encode()).hexdigest()
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha_criptografada))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

# Página: Cadastro de Alunos
def pagina_cadastro_alunos():
    st.title("Cadastro de Alunos")

    arquivo = st.file_uploader("Importar lista de alunos (.txt)", type="txt")

    if arquivo:
        conteudo = arquivo.read().decode("utf-8").splitlines()
        alunos = []

        for linha in conteudo[1:]:  # Ignorar o cabeçalho
            partes = linha.strip().split("\t")
            if len(partes) >= 3:
                cgm, nome, telefone = partes[0], partes[1], partes[2]
                alunos.append((cgm, nome, telefone))

        st.success(f"{len(alunos)} alunos importados!")

        st.dataframe(alunos, use_container_width=True)

        if st.button("Salvar no Banco de Dados"):
            conn = conectar()
            cursor = conn.cursor()
            for cgm, nome, telefone in alunos:
                cursor.execute("""
                    INSERT OR IGNORE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)
                """, (cgm, nome, telefone))
            conn.commit()
            conn.close()
            st.success("Alunos salvos com sucesso!")

# Página: Ocorrências
def pagina_ocorrencias():
    st.title("📋 Registro de Ocorrências Escolares")

    conn = conectar()
    cursor = conn.cursor()

    st.subheader("🔎 Buscar Ocorrências por CGM")
    cgm_busca = st.text_input("Digite o CGM do aluno para buscar ocorrências:")

    if cgm_busca:
        cursor.execute("SELECT * FROM ocorrencias WHERE cgm = ?", (cgm_busca,))
        resultados = cursor.fetchall()

        if resultados:
            for ocorrencia in resultados:
                st.markdown("---")
                st.write(f"**ID:** {ocorrencia[0]}")
                st.write(f"**CGM:** {ocorrencia[1]}")
                st.write(f"**Nome:** {ocorrencia[2]}")
                st.write(f"**Telefone:** {ocorrencia[3]}")
                st.write(f"**Data:** {ocorrencia[4]}")
                st.write(f"**Descrição:** {ocorrencia[5]}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✏️ Editar (ID {ocorrencia[0]})", key=f"editar_{ocorrencia[0]}"):
                        nova_descricao = st.text_area("Editar descrição:", ocorrencia[5], key=f"desc_{ocorrencia[0]}")
                        if st.button(f"Salvar Alteração (ID {ocorrencia[0]})", key=f"salvar_{ocorrencia[0]}"):
                            cursor.execute("UPDATE ocorrencias SET descricao = ? WHERE id = ?", (nova_descricao, ocorrencia[0]))
                            conn.commit()
                            st.success("Ocorrência atualizada com sucesso!")
                            st.experimental_rerun()

                with col2:
                    if st.button(f"🗑️ Excluir (ID {ocorrencia[0]})", key=f"excluir_{ocorrencia[0]}"):
                        cursor.execute("DELETE FROM ocorrencias WHERE id = ?", (ocorrencia[0],))
                        conn.commit()
                        st.warning("Ocorrência excluída com sucesso!")
                        st.experimental_rerun()

        else:
            st.info("Nenhuma ocorrência encontrada para este CGM.")

    st.markdown("---")
    st.subheader("➕ Registrar Nova Ocorrência")

    cgm_novo = st.text_input("CGM do aluno:")
    descricao_nova = st.text_area("Descrição da nova ocorrência:")

    if st.button("Salvar Nova Ocorrência"):
        cursor.execute("SELECT nome, telefone FROM alunos WHERE cgm = ?", (cgm_novo,))
        aluno = cursor.fetchone()

        if aluno:
            nome_aluno, telefone_aluno = aluno
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO ocorrencias (cgm, nome, telefone, data, descricao)
                VALUES (?, ?, ?, ?, ?)
            """, (cgm_novo, nome_aluno, telefone_aluno, data_atual, descricao_nova))
            conn.commit()
            st.success("Ocorrência registrada com sucesso!")
            st.experimental_rerun()
        else:
            st.error("Aluno não encontrado! Cadastre o aluno antes.")

    conn.close()

# Página: Lista de Alunos
def pagina_lista_alunos():
    st.title("Lista de Alunos Cadastrados")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT cgm, nome, telefone FROM alunos")
    alunos = cursor.fetchall()
    conn.close()

    if alunos:
        st.dataframe(alunos, use_container_width=True)
    else:
        st.warning("Nenhum aluno cadastrado ainda.")

# Página: Cadastro de Usuários
def pagina_cadastro_usuarios():
    st.title("Cadastro de Usuários")

    nome = st.text_input("Nome Completo")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    setor = st.text_input("Setor")

    if st.button("Cadastrar Usuário"):
        if nome and usuario and senha and setor:
            senha_criptografada = hashlib.sha256(senha.encode()).hexdigest()
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (nome, usuario, senha, setor) VALUES (?, ?, ?, ?)
            """, (nome, usuario, senha_criptografada, setor))
            conn.commit()
            conn.close()
            st.success(f"Usuário '{usuario}' cadastrado com sucesso!")
        else:
            st.warning("Preencha todos os campos!")

# Menu lateral
def menu_principal():
    st.sidebar.title("Menu")
    pagina = st.sidebar.selectbox("Escolha a Página", [
        "Cadastro de Alunos", 
        "Ocorrências", 
        "Lista de Alunos", 
        "Cadastro de Usuários"
    ])

    if pagina == "Cadastro de Alunos":
        pagina_cadastro_alunos()
    elif pagina == "Ocorrências":
        pagina_ocorrencias()
    elif pagina == "Lista de Alunos":
        pagina_lista_alunos()
    elif pagina == "Cadastro de Usuários":
        pagina_cadastro_usuarios()

# Controle de sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    login_usuario = st.text_input("Usuário")
    login_senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if verificar_login(login_usuario, login_senha):
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")
else:
    menu_principal()
