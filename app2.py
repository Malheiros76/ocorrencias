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

# Função de conexão com o banco
def conectar():
    return sqlite3.connect("ocorrencias.db", check_same_thread=False)

# Inicialização do banco
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
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            usuario TEXT UNIQUE,
            senha TEXT,
            nivel TEXT,
            setor TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT,
            nome TEXT,
            telefone TEXT,
            responsavel TEXT,
            data TEXT,
            turma TEXT,
            descricao TEXT
        )
    """)
    conn.commit()
    conn.close()

# Backup automático
def backup_automatico():
    if not os.path.exists("backups"):
        os.mkdir("backups")
    hoje = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy("ocorrencias.db", f"backups/ocorrencias_backup_{hoje}.db")
    # Limpeza de backups antigos
    for arquivo in os.listdir("backups"):
        caminho = os.path.join("backups", arquivo)
        if os.path.isfile(caminho):
            data_criacao = datetime.fromtimestamp(os.path.getctime(caminho))
            if datetime.now() - data_criacao > timedelta(days=7):
                os.remove(caminho)

# Função de login
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
            st.session_state['nivel'] = resultado[4]
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")

# Tela de cadastro de alunos
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
            st.success("Aluno salvo!")
    st.subheader("Importar alunos via TXT")
    arquivo = st.file_uploader("Selecionar arquivo TXT", type="txt")
    if arquivo:
        df = pd.read_csv(arquivo, sep=",", header=None, names=["cgm", "nome", "telefone"])
        st.dataframe(df)
        if st.button("Importar do TXT"):
            conn = conectar()
            cursor = conn.cursor()
            for _, row in df.iterrows():
                cursor.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (row["cgm"], row["nome"], row["telefone"]))
            conn.commit()
            conn.close()
            st.success("Importado com sucesso!")

# Tela de cadastro de usuários
def pagina_cadastro_usuario():
    st.header("Cadastro de Usuário 🧑‍💼")
    nome = st.text_input("Nome completo")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    nivel = st.selectbox("Nível de acesso", ["admin", "user"])
    setor = st.text_input("Setor")
    if st.button("Cadastrar Usuário"):
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nome, usuario, senha, nivel, setor) VALUES (?, ?, ?, ?, ?)", (nome, usuario, senha, nivel, setor))
            conn.commit()
            st.success("Usuário cadastrado!")
        except:
            st.error("Usuário já existe!")
        finally:
            conn.close()

# Tela de lista de alunos
def pagina_lista_alunos():
    st.header("Lista de Alunos 📄")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alunos ORDER BY nome ASC")
    dados = cursor.fetchall()
    conn.close()
    if dados:
        st.dataframe(pd.DataFrame(dados, columns=["CGM", "Nome", "Telefone"]))
    else:
        st.info("Nenhum aluno cadastrado.")

# Tela de ocorrências
def pagina_ocorrencias():
    st.header("Registro de Ocorrências 📋")
    cgm = st.text_input("CGM do aluno")
    nome = telefone = ""
    if cgm:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, telefone FROM alunos WHERE cgm=?", (cgm,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            nome, telefone = resultado
            st.info(f"Nome: {nome} | Telefone: {telefone}")
    descricao = st.text_area("Descrição da Ocorrência")
    if st.button("Salvar Ocorrência"):
        if cgm and descricao:
            backup_automatico()
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ocorrencias (cgm, nome, telefone, data, descricao) VALUES (?, ?, ?, ?, ?)", (cgm, nome, telefone, data_hora, descricao))
            conn.commit()
            conn.close()
            st.success("Ocorrência salva!")

# Tela de exportação
def pagina_exportar():
    st.header("Exportar Relatórios 📄")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT cgm, nome, data, descricao, telefone FROM ocorrencias ORDER BY nome, data")
    dados = cursor.fetchall()
    conn.close()
    if not dados:
        st.warning("Nenhuma ocorrência para exportar.")
        return
    if st.button("Exportar Word Completo"):
        doc = Document()
        try:
            doc.add_picture("CABEÇARIOAPP.png", width=doc.sections[0].page_width)
        except:
            pass
        doc.add_heading("Relatório Completo", 0)
        for cgm, nome, data, desc, telefone in dados:
            doc.add_paragraph(f"CGM: {cgm}\nNome: {nome}\nData: {data}\nTelefone: {telefone}\nDescrição: {desc}\n----------------------")
        doc.add_paragraph("\nAssinatura Servidor: __________  Assinatura Responsável: __________")
        caminho = "relatorio_completo.docx"
        doc.save(caminho)
        with open(caminho, "rb") as f:
            st.download_button("📥 Baixar Word", f, file_name=caminho)

# Menu lateral
def menu():
    st.sidebar.image("BRASÃO.png", width=200)
    opcoes = ["Cadastro de Alunos", "Ocorrências", "Exportar Relatórios", "Cadastro de Usuário", "Lista de Alunos"]
    escolha = st.sidebar.selectbox("Menu", opcoes)
    if escolha == "Cadastro de Alunos":
        pagina_cadastro_alunos()
    elif escolha == "Ocorrências":
        pagina_ocorrencias()
    elif escolha == "Exportar Relatórios":
        pagina_exportar()
    elif escolha == "Cadastro de Usuário":
        pagina_cadastro_usuario()
    elif escolha == "Lista de Alunos":
        pagina_lista_alunos()

# Execução principal
inicializar_db()
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if not st.session_state["logado"]:
    login()
else:
    menu()
