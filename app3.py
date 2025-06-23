import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import urllib.parse
import os
import shutil

def conectar():
    return sqlite3.connect("ocorrencias.db", check_same_thread=False)

def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            cgm TEXT PRIMARY KEY,
            nome TEXT,
            telefone TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT,
            nome TEXT,
            telefone TEXT,
            data TEXT,
            descricao TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            usuario TEXT UNIQUE,
            senha TEXT,
            setor TEXT
        )
    """)
    conn.commit()
    conn.close()

def criar_backup():
    if not os.path.exists("backups"):
        os.makedirs("backups")
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy("ocorrencias.db", f"backups/backup_{agora}.db")

def excluir_backups_antigos():
    pasta = "backups"
    limite = datetime.now() - timedelta(days=7)
    if os.path.exists(pasta):
        for arquivo in os.listdir(pasta):
            caminho = os.path.join(pasta, arquivo)
            if os.path.isfile(caminho):
                tempo_modificacao = datetime.fromtimestamp(os.path.getmtime(caminho))
                if tempo_modificacao < limite:
                    os.remove(caminho)

def login():
    st.title("Login 👤")
    usuario = st.text_input("Usuário", key="login_usuario")
    senha = st.text_input("Senha", type="password", key="login_senha")
    if st.button("Entrar", key="btn_login"):

def pagina_cadastro_alunos():
    st.header("Cadastro de Alunos 👦👧")

    cgm = st.text_input("CGM", key="cadastro_cgm")
    nome = st.text_input("Nome", key="cadastro_nome")
    data_nascimento = st.date_input("Data de Nascimento", key="cadastro_data_nasc")
    telefone = st.text_input("Telefone", key="cadastro_telefone")
    responsavel = st.text_input("Responsável", key="cadastro_responsavel")
    data = st.date_input("Data de Cadastro", key="cadastro_data_cadastro")
    turma = st.text_input("Turma", key="cadastro_turma")

    if st.button("Salvar Aluno", key="btn_salvar_aluno"):
        # código...
           if cgm and nome:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (cgm, nome, telefone))
            conn.commit()
            conn.close()
            st.success("Aluno salvo com sucesso!")

    arquivo_txt = st.file_uploader("Importar alunos via TXT", type=["txt"])
    if arquivo_txt:
        df = pd.read_csv(arquivo_txt, sep=",", header=None, names=["CGM", "Nome", "Telefone"])
        st.dataframe(df)
        if st.button("Importar do TXT"):
            conn = conectar()
            cursor = conn.cursor()
            for _, row in df.iterrows():
                cursor.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (row["CGM"], row["Nome"], row["Telefone"]))
            conn.commit()
            conn.close()
            st.success("Importação concluída!")

def pagina_lista_alunos():
    st.header("📄 Lista de Alunos")
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)
    conn.close()
    st.dataframe(df)

def pagina_cadastro_usuario():
    st.header("Cadastro de Usuário 🧑‍💼")
    nome = st.text_input("Nome completo")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    setor = st.text_input("Setor")
    if st.button("Cadastrar"):
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nome, usuario, senha, setor) VALUES (?, ?, ?, ?)", (nome, usuario, senha, setor))
            conn.commit()
            st.success("Usuário cadastrado!")
        except sqlite3.IntegrityError:
            st.error("Usuário já existe!")
        conn.close()

def pagina_ocorrencias():
    st.header("Registro de Ocorrências 📋")
    cgm = st.text_input("CGM do aluno")
    nome, telefone = "", ""
    if cgm:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, telefone FROM alunos WHERE cgm=?", (cgm,))
        res = cursor.fetchone()
        conn.close()
        if res:
            nome, telefone = res
            st.info(f"Aluno: {nome} | Telefone: {telefone}")

    descricao = st.text_area("Descrição da Ocorrência")

    if st.button("Salvar Ocorrência"):
        if cgm and descricao:
            criar_backup()
            excluir_backups_antigos()
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ocorrencias (cgm, nome, telefone, data, descricao) VALUES (?, ?, ?, ?, ?)",
                           (cgm, nome, telefone, data_atual, descricao))
            conn.commit()
            conn.close()
            st.success("Ocorrência salva!")
            st.session_state['pagina'] = "Ocorrências"
            st.experimental_rerun()

    conn = conectar()
    df = pd.read_sql_query("SELECT id, cgm, nome, data, descricao FROM ocorrencias ORDER BY data DESC", conn)
    conn.close()

    for _, row in df.iterrows():
        with st.expander(f"{row['id']} - {row['nome']} - {row['data']}"):
            st.write(row['descricao'])
            if st.button(f"Excluir {row['id']}"):
                criar_backup()
                excluir_backups_antigos()
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ocorrencias WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.warning("Ocorrência excluída!")
                st.session_state['pagina'] = "Ocorrências"
                st.experimental_rerun()

def pagina_exportar():
    st.header("Exportar Relatórios 📄")
    conn = conectar()
    df = pd.read_sql_query("SELECT cgm, nome, data, descricao FROM ocorrencias ORDER BY nome, data", conn)
    conn.close()

    if df.empty:
        st.warning("Nenhuma ocorrência para exportar.")
        return

    opcao = st.radio("Tipo de Exportação:", ["Word", "PDF"])

    if st.button("Exportar"):
        if opcao == "Word":
            doc = Document()
            doc.add_heading("Relatório de Ocorrências", 0)
            for _, row in df.iterrows():
                doc.add_paragraph(f"CGM: {row['cgm']}\nNome: {row['nome']}\nData: {row['data']}\nDescrição: {row['descricao']}\n-----")
            doc_path = "relatorio_ocorrencias.docx"
            doc.save(doc_path)
            with open(doc_path, "rb") as f:
                st.download_button("📥 Baixar Word", f, file_name=doc_path)

        if opcao == "PDF":
            pdf_path = "relatorio_ocorrencias.pdf"
            c = canvas.Canvas(pdf_path, pagesize=A4)
            y = 800
            for _, row in df.iterrows():
                texto = f"CGM: {row['cgm']}\nNome: {row['nome']}\nData: {row['data']}\nDescrição: {row['descricao']}\n-----\n"
                for linha in texto.split('\n'):
                    c.drawString(50, y, linha)
                    y -= 15
                    if y < 80:
                        c.showPage()
                        y = 800
            c.save()
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Baixar PDF", f, file_name=pdf_path)

def menu():
    st.sidebar.image("BRASÃO.png", width=200)
    opcao = st.sidebar.selectbox("Menu", ["Cadastro de Alunos", "Lista de Alunos", "Ocorrências", "Exportar Relatórios", "Cadastro de Usuário"], key="menu_principal")

    if opcao == "Cadastro de Alunos":
        pagina_cadastro_alunos()
    elif opcao == "Lista de Alunos":
        pagina_lista_alunos()
    elif opcao == "Ocorrências":
        pagina_ocorrencias()
    elif opcao == "Exportar Relatórios":
        pagina_exportar()
    elif opcao == "Cadastro de Usuário":
        pagina_cadastro_usuario()

# Execução
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Login"

inicializar_db()

if not st.session_state["logado"]:
    login()
else:
    menu()
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import urllib.parse
import os
import shutil

def conectar():
    return sqlite3.connect("ocorrencias.db", check_same_thread=False)

def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            cgm TEXT PRIMARY KEY,
            nome TEXT,
            telefone TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT,
            nome TEXT,
            telefone TEXT,
            data TEXT,
            descricao TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            usuario TEXT UNIQUE,
            senha TEXT,
            setor TEXT
        )
    """)
    conn.commit()
    conn.close()

def criar_backup():
    if not os.path.exists("backups"):
        os.makedirs("backups")
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy("ocorrencias.db", f"backups/backup_{agora}.db")

def excluir_backups_antigos():
    pasta = "backups"
    limite = datetime.now() - timedelta(days=7)
    if os.path.exists(pasta):
        for arquivo in os.listdir(pasta):
            caminho = os.path.join(pasta, arquivo)
            if os.path.isfile(caminho):
                tempo_modificacao = datetime.fromtimestamp(os.path.getmtime(caminho))
                if tempo_modificacao < limite:
                    os.remove(caminho)

def login():
    st.title("Login 👤")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            st.session_state['logado'] = True
            st.session_state['pagina'] = "Menu"
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos!")

def pagina_cadastro_alunos():
    st.header("Cadastro de Alunos 👦👧")
    cgm = st.text_input("CGM")
    nome = st.text_input("Nome")
    telefone = st.text_input("Telefone")

    if st.button("Salvar Aluno"):
        if cgm and nome:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (cgm, nome, telefone))
            conn.commit()
            conn.close()
            st.success("Aluno salvo com sucesso!")

    arquivo_txt = st.file_uploader("Importar alunos via TXT", type=["txt"])
    if arquivo_txt:
        df = pd.read_csv(arquivo_txt, sep=",", header=None, names=["CGM", "Nome", "Telefone"])
        st.dataframe(df)
        if st.button("Importar do TXT"):
            conn = conectar()
            cursor = conn.cursor()
            for _, row in df.iterrows():
                cursor.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (row["CGM"], row["Nome"], row["Telefone"]))
            conn.commit()
            conn.close()
            st.success("Importação concluída!")

def pagina_lista_alunos():
    st.header("📄 Lista de Alunos")
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)
    conn.close()
    st.dataframe(df)

def pagina_cadastro_usuario():
    st.header("Cadastro de Usuário 🧑‍💼")
    nome = st.text_input("Nome completo")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    setor = st.text_input("Setor")
    if st.button("Cadastrar"):
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nome, usuario, senha, setor) VALUES (?, ?, ?, ?)", (nome, usuario, senha, setor))
            conn.commit()
            st.success("Usuário cadastrado!")
        except sqlite3.IntegrityError:
            st.error("Usuário já existe!")
        conn.close()

def pagina_ocorrencias():
    st.header("Registro de Ocorrências 📋")
    cgm = st.text_input("CGM do aluno")
    nome, telefone = "", ""
    if cgm:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, telefone FROM alunos WHERE cgm=?", (cgm,))
        res = cursor.fetchone()
        conn.close()
        if res:
            nome, telefone = res
            st.info(f"Aluno: {nome} | Telefone: {telefone}")

    descricao = st.text_area("Descrição da Ocorrência")

    if st.button("Salvar Ocorrência"):
        if cgm and descricao:
            criar_backup()
            excluir_backups_antigos()
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ocorrencias (cgm, nome, telefone, data, descricao) VALUES (?, ?, ?, ?, ?)",
                           (cgm, nome, telefone, data_atual, descricao))
            conn.commit()
            conn.close()
            st.success("Ocorrência salva!")
            st.session_state['pagina'] = "Ocorrências"
            st.experimental_rerun()

    conn = conectar()
    df = pd.read_sql_query("SELECT id, cgm, nome, data, descricao FROM ocorrencias ORDER BY data DESC", conn)
    conn.close()

    for _, row in df.iterrows():
        with st.expander(f"{row['id']} - {row['nome']} - {row['data']}"):
            st.write(row['descricao'])
            if st.button(f"Excluir {row['id']}"):
                criar_backup()
                excluir_backups_antigos()
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ocorrencias WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.warning("Ocorrência excluída!")
                st.session_state['pagina'] = "Ocorrências"
                st.experimental_rerun()

def pagina_exportar():
    st.header("Exportar Relatórios 📄")
    conn = conectar()
    df = pd.read_sql_query("SELECT cgm, nome, data, descricao FROM ocorrencias ORDER BY nome, data", conn)
    conn.close()

    if df.empty:
        st.warning("Nenhuma ocorrência para exportar.")
        return

    opcao = st.radio("Tipo de Exportação:", ["Word", "PDF"])

    if st.button("Exportar"):
        if opcao == "Word":
            doc = Document()
            doc.add_heading("Relatório de Ocorrências", 0)
            for _, row in df.iterrows():
                doc.add_paragraph(f"CGM: {row['cgm']}\nNome: {row['nome']}\nData: {row['data']}\nDescrição: {row['descricao']}\n-----")
            doc_path = "relatorio_ocorrencias.docx"
            doc.save(doc_path)
            with open(doc_path, "rb") as f:
                st.download_button("📥 Baixar Word", f, file_name=doc_path)

        if opcao == "PDF":
            pdf_path = "relatorio_ocorrencias.pdf"
            c = canvas.Canvas(pdf_path, pagesize=A4)
            y = 800
            for _, row in df.iterrows():
                texto = f"CGM: {row['cgm']}\nNome: {row['nome']}\nData: {row['data']}\nDescrição: {row['descricao']}\n-----\n"
                for linha in texto.split('\n'):
                    c.drawString(50, y, linha)
                    y -= 15
                    if y < 80:
                        c.showPage()
                        y = 800
            c.save()
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Baixar PDF", f, file_name=pdf_path)

def menu():
    st.sidebar.image("BRASÃO.png", width=200)
    opcao = st.sidebar.selectbox("Menu", ["Cadastro de Alunos", "Lista de Alunos", "Ocorrências", "Exportar Relatórios", "Cadastro de Usuário"])

    if opcao == "Cadastro de Alunos":
        pagina_cadastro_alunos()
    elif opcao == "Lista de Alunos":
        pagina_lista_alunos()
    elif opcao == "Ocorrências":
        pagina_ocorrencias()
    elif opcao == "Exportar Relatórios":
        pagina_exportar()
    elif opcao == "Cadastro de Usuário":
        pagina_cadastro_usuario()

# Execução
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Login"

inicializar_db()

if not st.session_state["logado"]:
    login()
else:
    menu()
