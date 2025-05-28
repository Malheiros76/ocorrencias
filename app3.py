import streamlit as st
import sqlite3
import pandas as pd
import os

# Inicializa a sessão
if "cgm" not in st.session_state:
    st.session_state["cgm"] = ""
if "nome_aluno" not in st.session_state:
    st.session_state["nome_aluno"] = ""
if "nome_responsavel" not in st.session_state:
    st.session_state["nome_responsavel"] = ""
if "telefone_responsavel" not in st.session_state:
    st.session_state["telefone_responsavel"] = ""

# Conexão com o banco de dados
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

# Criação das tabelas
c.execute('''CREATE TABLE IF NOT EXISTS ocorrencias (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             cgm TEXT,
             nome_aluno TEXT,
             nome_responsavel TEXT,
             telefone_responsavel TEXT,
             turma TEXT,
             ano TEXT,
             data TEXT,
             fatos TEXT
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS alunos (
             cgm TEXT PRIMARY KEY,
             nome_aluno TEXT,
             telefone TEXT
             )''')

conn.commit()

# Função para salvar ocorrência
def salvar_ocorrencia(cgm, nome_aluno, nome_responsavel, telefone_responsavel, turma, ano, data, fatos):
    c.execute("INSERT INTO ocorrencias (cgm, nome_aluno, nome_responsavel, telefone_responsavel, turma, ano, data, fatos) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (cgm, nome_aluno, nome_responsavel, telefone_responsavel, turma, ano, data, fatos))
    conn.commit()

# Função para buscar aluno pelo CGM
def buscar_aluno_por_cgm(cgm):
    c.execute("SELECT nome_aluno, telefone FROM alunos WHERE cgm = ?", (cgm,))
    return c.fetchone()

# Função para buscar ocorrências por CGM
def buscar_ocorrencias(cgm):
    c.execute("SELECT data, fatos FROM ocorrencias WHERE cgm = ?", (cgm,))
    return c.fetchall()

# Função para importar alunos do arquivo
def importar_alunos(arquivo):
    try:
        df = pd.read_csv(arquivo, sep="\t", engine="python", names=["cgm", "nome_aluno", "telefone"], skiprows=1)
        for _, row in df.iterrows():
            c.execute("INSERT OR REPLACE INTO alunos (cgm, nome_aluno, telefone) VALUES (?, ?, ?)",
                      (str(row["cgm"]).strip(), str(row["nome_aluno"]).strip(), str(row["telefone"]).strip()))
        conn.commit()
        st.success("Alunos importados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao importar alunos: {e}")

# Interface
st.title("Registro de Ocorrências - CCMLC")

aba = st.sidebar.radio("Menu", ["Registrar Ocorrência", "Consultar Ocorrências", "Importar Alunos"])

if aba == "Registrar Ocorrência":
    st.subheader("Registrar Ocorrência")

    st.session_state["cgm"] = st.text_input("CGM", value=st.session_state["cgm"])

    # Busca automática de nome e telefone ao digitar o CGM
    if st.session_state["cgm"]:
        resultado_aluno = buscar_aluno_por_cgm(st.session_state["cgm"])
        if resultado_aluno:
            nome_aluno, telefone = resultado_aluno
            if not st.session_state["nome_aluno"]:
                st.session_state["nome_aluno"] = nome_aluno
            if not st.session_state["telefone_responsavel"]:
                st.session_state["telefone_responsavel"] = telefone

    st.session_state["nome_aluno"] = st.text_input("Nome do aluno", value=st.session_state["nome_aluno"])
    st.session_state["nome_responsavel"] = st.text_input("Nome do responsável", value=st.session_state["nome_responsavel"])
    st.session_state["telefone_responsavel"] = st.text_input("Telefone do responsável", value=st.session_state["telefone_responsavel"])
    turma = st.text_input("Turma")
    ano = st.text_input("Ano")
    data = st.date_input("Data")
    fatos = st.text_area("Fatos ocorridos")

    if st.button("Salvar"):
        salvar_ocorrencia(st.session_state["cgm"], st.session_state["nome_aluno"], st.session_state["nome_responsavel"],
                          st.session_state["telefone_responsavel"], turma, ano, str(data), fatos)
        st.success("Ocorrência registrada com sucesso!")

        # Limpar os campos
        st.session_state["cgm"] = ""
        st.session_state["nome_aluno"] = ""
        st.session_state["nome_responsavel"] = ""
        st.session_state["telefone_responsavel"] = ""

elif aba == "Consultar Ocorrências":
    st.subheader("Consultar Ocorrências por CGM")
    cgm_consulta = st.text_input("Digite o CGM do aluno para consulta:")
    if cgm_consulta:
        resultados = buscar_ocorrencias(cgm_consulta)
        if resultados:
            df_resultado = pd.DataFrame(resultados, columns=["Data", "Fatos"])
            st.dataframe(df_resultado)
        else:
            st.warning("Nenhuma ocorrência encontrada para este CGM.")

elif aba == "Importar Alunos":
    st.subheader("Importar lista de alunos (.txt)")
    arquivo = st.file_uploader("Escolha o arquivo .txt com os dados dos alunos", type=["txt"])
    if arquivo is not None:
        importar_alunos(arquivo)
