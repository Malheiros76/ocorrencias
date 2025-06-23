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
import glob

# ========== Função de Conexão ==========
def conectar():
    return sqlite3.connect("ocorrencias.db", check_same_thread=False)

# ========== Inicializar Banco ==========
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

# ========== Função de Backup ==========
def fazer_backup():
    if not os.path.exists("backups"):
        os.makedirs("backups")
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy("ocorrencias.db", f"backups/ocorrencias_backup_{agora}.db")

def limpar_backups_antigos():
    sete_dias_atras = datetime.now() - timedelta(days=7)
    for arquivo in glob.glob("backups/ocorrencias_backup_*.db"):
        timestamp_str = arquivo.split("_backup_")[1].replace(".db", "")
        try:
            data_arquivo = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            if data_arquivo < sete_dias_atras:
                os.remove(arquivo)
        except:
            pass

# ========== Função de Login ==========
def login():
    st.title("Login 👤")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        if cursor.fetchone():
            st.session_state["logado"] = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")
        conn.close()

# ========== Função Cadastro de Alunos ==========
def pagina_cadastro_alunos():
    st.header("Cadastro de Alunos 👦👧")
    cgm = st.text_input("CGM")
    nome = st.text_input("Nome")
    telefone = st.text_input("Telefone")
    if st.button("Salvar Aluno"):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO alunos VALUES (?, ?, ?)", (cgm, nome, telefone))
        conn.commit()
        conn.close()
        st.success("Aluno salvo!")

    st.subheader("Importar Alunos via TXT")
    arquivo_txt = st.file_uploader("Escolha o TXT", type=["txt"])
    if arquivo_txt and st.button("Importar Alunos"):
        df = pd.read_csv(arquivo_txt, sep=",", names=["CGM", "Nome", "Telefone"], header=None)
        conn = conectar()
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("INSERT OR REPLACE INTO alunos VALUES (?, ?, ?)", (row["CGM"], row["Nome"], row["Telefone"]))
        conn.commit()
        conn.close()
        st.success("Importação concluída!")

# ========== Função Registro de Ocorrências ==========
def pagina_ocorrencias():
    st.header("Registro de Ocorrências 📋")
    cgm = st.text_input("CGM do Aluno")
    conn = conectar()
    cursor = conn.cursor()
    nome = telefone = ""
    if cgm:
        cursor.execute("SELECT nome, telefone FROM alunos WHERE cgm=?", (cgm,))
        resultado = cursor.fetchone()
        if resultado:
            nome, telefone = resultado
            st.info(f"Nome: {nome} | Telefone: {telefone}")

    descricao = st.text_area("Descrição da Ocorrência")

    if st.button("Salvar Ocorrência"):
        if cgm and descricao:
            fazer_backup()
            limpar_backups_antigos()
            data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO ocorrencias (cgm, nome, telefone, data, descricao) VALUES (?, ?, ?, ?, ?)", (cgm, nome, telefone, data, descricao))
            conn.commit()
            st.success("Ocorrência salva!")

    st.subheader("Lista de Ocorrências")
    cursor.execute("SELECT id, cgm, nome, data, descricao FROM ocorrencias ORDER BY data DESC")
    ocorrencias = cursor.fetchall()
    for id, cgm, nome, data, desc in ocorrencias:
        with st.expander(f"{id} - {nome} ({data})"):
            st.write(desc)
            col1, col2 = st.columns(2)
            if col1.button(f"Alterar {id}"):
                nova = st.text_area(f"Nova descrição {id}", value=desc, key=f"alt_{id}")
                if col1.button(f"Salvar {id}"):
                    cursor.execute("UPDATE ocorrencias SET descricao=? WHERE id=?", (nova, id))
                    conn.commit()
                    st.success("Alterado!")
                    st.experimental_rerun()
            if col2.button(f"Excluir {id}"):
                fazer_backup()
                limpar_backups_antigos()
                cursor.execute("DELETE FROM ocorrencias WHERE id=?", (id,))
                conn.commit()
                st.success("Excluído!")
                st.experimental_rerun()
    conn.close()

# ========== Função Exportação ==========
def pagina_exportar():
    st.header("Exportar Relatório 📄")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT cgm, nome, data, descricao, telefone FROM ocorrencias ORDER BY nome, data")
    ocorrencias = cursor.fetchall()
    conn.close()

    if not ocorrencias:
        st.warning("Sem ocorrências para exportar.")
        return

    doc = Document()
    try:
        doc.add_picture("CABEÇARIOAPP.png", width=doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin)
    except:
        pass
    doc.add_heading("Relatório de Ocorrências", 0)
    for cgm, nome, data, desc, telefone in ocorrencias:
        doc.add_paragraph(f"CGM: {cgm}\nNome: {nome}\nData: {data}\nTelefone: {telefone}\nDescrição: {desc}\n----------------------")
    caminho_word = "relatorio_ocorrencias.docx"
    doc.save(caminho_word)
    with open(caminho_word, "rb") as f:
        st.download_button("📥 Baixar Word", f, file_name=caminho_word)

# ========== Função Cadastro de Usuário ==========
def pagina_cadastro_usuario():
    st.header("Cadastro de Usuário 🧑‍💼")
    nome = st.text_input("Nome")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    setor = st.text_input("Setor")
    if st.button("Cadastrar"):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nome, usuario, senha, setor) VALUES (?, ?, ?, ?)", (nome, usuario, senha, setor))
        conn.commit()
        conn.close()
        st.success("Usuário cadastrado!")

# ========== Função Lista de Alunos ==========
def pagina_lista_alunos():
    st.header("Lista de Alunos 📄")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT cgm, nome, telefone FROM alunos ORDER BY nome")
    alunos = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(alunos, columns=["CGM", "Nome", "Telefone"])
    st.dataframe(df)

# ========== Menu Principal ==========
def menu():
    st.sidebar.image("BRASÃO.png", width=200)
    pagina = st.sidebar.selectbox("Menu", ["Cadastro de Alunos", "Ocorrências", "Exportar Relatórios", "Cadastro de Usuário", "Lista de Alunos"])
    if pagina == "Cadastro de Alunos":
        pagina_cadastro_alunos()
    elif pagina == "Ocorrências":
        pagina_ocorrencias()
    elif pagina == "Exportar Relatórios":
        pagina_exportar()
    elif pagina == "Cadastro de Usuário":
        pagina_cadastro_usuario()
    elif pagina == "Lista de Alunos":
        pagina_lista_alunos()

# ========== Execução ==========
inicializar_db()
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    login()
else:
    menu()
