import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- Banco de dados ---

def criar_tabelas(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            cgm TEXT PRIMARY KEY,
            nome TEXT,
            telefone TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT,
            nome TEXT,
            telefone TEXT,
            turma TEXT,
            ano TEXT,
            data TEXT,
            fatos TEXT,
            FOREIGN KEY (cgm) REFERENCES alunos(cgm)
        )
    ''')
    conn.commit()

def inserir_alunos(conn, df_alunos):
    c = conn.cursor()
    for _, row in df_alunos.iterrows():
        try:
            c.execute('''
                INSERT OR IGNORE INTO alunos (cgm, nome, telefone)
                VALUES (?, ?, ?)
            ''', (str(row['CGM']).strip(), row['Nome do Estudante'].strip(), row['Telefone'].strip()))
        except Exception as e:
            st.warning(f"Erro ao inserir aluno {row['Nome do Estudante']}: {e}")
    conn.commit()

def buscar_aluno(conn, cgm):
    c = conn.cursor()
    c.execute('SELECT cgm, nome, telefone FROM alunos WHERE cgm = ?', (cgm,))
    return c.fetchone()

def inserir_ocorrencia(conn, ocorrencia):
    c = conn.cursor()
    c.execute('''
        INSERT INTO ocorrencias (cgm, nome, telefone, turma, ano, data, fatos)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        ocorrencia['CGM'],
        ocorrencia['Nome do Estudante'],
        ocorrencia['Telefone'],
        ocorrencia['Turma'],
        ocorrencia['Ano'],
        ocorrencia['Data'],
        ocorrencia['Fatos']
    ))
    conn.commit()

def listar_ocorrencias(conn):
    c = conn.cursor()
    c.execute('SELECT id, cgm, nome, telefone, turma, ano, data, fatos FROM ocorrencias ORDER BY data DESC')
    rows = c.fetchall()
    cols = ['ID', 'CGM', 'Nome', 'Telefone', 'Turma', 'Ano', 'Data', 'Fatos']
    return pd.DataFrame(rows, columns=cols)

# --- Streamlit App ---

st.title("Sistema de Registro de Ocorrências com SQLite")

# Conectar banco de dados
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
criar_tabelas(conn)

menu = st.sidebar.selectbox("Menu", ["Importar Lista de Alunos", "Registrar Ocorrência"])

if menu == "Importar Lista de Alunos":
    st.header("Importar arquivo TXT com alunos")

    uploaded_file = st.file_uploader("Envie seu arquivo .txt", type=["txt"])
    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            df = pd.read_csv(pd.io.common.StringIO(content), sep="\t", engine='python')
            # Limpa colunas vazias
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            st.dataframe(df)

            if st.button("Salvar alunos no banco"):
                inserir_alunos(conn, df)
                st.success("Alunos importados e salvos no banco de dados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

elif menu == "Registrar Ocorrência":
    st.header("Registrar ocorrência para aluno")

    cgm_input = st.text_input("Digite o CGM do aluno")

    nome_estudante = ""
    telefone = ""

    if cgm_input:
        aluno = buscar_aluno(conn, cgm_input.strip())
        if aluno:
            nome_estudante = aluno[1]
            telefone = aluno[2]
        else:
            st.warning("CGM não encontrado na base de alunos. Importe a lista de alunos primeiro.")

    st.text_input("Nome do Estudante", value=nome_estudante, key="nome_estudante")
    st.text_input("Telefone", value=telefone, key="telefone")
    turma = st.text_input("Turma")
    ano = st.text_input("Ano")
    data = st.date_input("Data")
    fatos = st.text_area("Descrição da Ocorrência")

    if st.button("Registrar Ocorrência"):
        if not cgm_input or not nome_estudante or not fatos:
            st.error("Preencha CGM, Nome do Estudante e descrição da ocorrência.")
        else:
            ocorrencia = {
                "CGM": cgm_input.strip(),
                "Nome do Estudante": nome_estudante,
                "Telefone": telefone,
                "Turma": turma,
                "Ano": ano,
                "Data": data.strftime("%Y-%m-%d"),
                "Fatos": fatos,
            }
            inserir_ocorrencia(conn, ocorrencia)
            st.success("Ocorrência registrada com sucesso!")
            st.experimental_rerun()

    st.subheader("Ocorrências registradas")
    df_ocorrencias = listar_ocorrencias(conn)
    if not df_ocorrencias.empty:
        st.dataframe(df_ocorrencias)
    else:
        st.info("Nenhuma ocorrência registrada ainda.")
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- Banco de dados ---

def criar_tabelas(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            cgm TEXT PRIMARY KEY,
            nome TEXT,
            telefone TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT,
            nome TEXT,
            telefone TEXT,
            turma TEXT,
            ano TEXT,
            data TEXT,
            fatos TEXT,
            FOREIGN KEY (cgm) REFERENCES alunos(cgm)
        )
    ''')
    conn.commit()

def inserir_alunos(conn, df_alunos):
    c = conn.cursor()
    for _, row in df_alunos.iterrows():
        try:
            c.execute('''
                INSERT OR IGNORE INTO alunos (cgm, nome, telefone)
                VALUES (?, ?, ?)
            ''', (str(row['CGM']).strip(), row['Nome do Estudante'].strip(), row['Telefone'].strip()))
        except Exception as e:
            st.warning(f"Erro ao inserir aluno {row['Nome do Estudante']}: {e}")
    conn.commit()

def buscar_aluno(conn, cgm):
    c = conn.cursor()
    c.execute('SELECT cgm, nome, telefone FROM alunos WHERE cgm = ?', (cgm,))
    return c.fetchone()

def inserir_ocorrencia(conn, ocorrencia):
    c = conn.cursor()
    c.execute('''
        INSERT INTO ocorrencias (cgm, nome, telefone, turma, ano, data, fatos)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        ocorrencia['CGM'],
        ocorrencia['Nome do Estudante'],
        ocorrencia['Telefone'],
        ocorrencia['Turma'],
        ocorrencia['Ano'],
        ocorrencia['Data'],
        ocorrencia['Fatos']
    ))
    conn.commit()

def listar_ocorrencias(conn):
    c = conn.cursor()
    c.execute('SELECT id, cgm, nome, telefone, turma, ano, data, fatos FROM ocorrencias ORDER BY data DESC')
    rows = c.fetchall()
    cols = ['ID', 'CGM', 'Nome', 'Telefone', 'Turma', 'Ano', 'Data', 'Fatos']
    return pd.DataFrame(rows, columns=cols)

# --- Streamlit App ---

st.title("Sistema de Registro de Ocorrências com SQLite")

# Conectar banco de dados
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
criar_tabelas(conn)

menu = st.sidebar.selectbox("Menu", ["Importar Lista de Alunos", "Registrar Ocorrência"])

if menu == "Importar Lista de Alunos":
    st.header("Importar arquivo TXT com alunos")

    uploaded_file = st.file_uploader("Envie seu arquivo .txt", type=["txt"])
    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            df = pd.read_csv(pd.io.common.StringIO(content), sep="\t", engine='python')
            # Limpa colunas vazias
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            st.dataframe(df)

            if st.button("Salvar alunos no banco"):
                inserir_alunos(conn, df)
                st.success("Alunos importados e salvos no banco de dados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

elif menu == "Registrar Ocorrência":
    st.header("Registrar ocorrência para aluno")

    cgm_input = st.text_input("Digite o CGM do aluno")

    nome_estudante = ""
    telefone = ""

    if cgm_input:
        aluno = buscar_aluno(conn, cgm_input.strip())
        if aluno:
            nome_estudante = aluno[1]
            telefone = aluno[2]
        else:
            st.warning("CGM não encontrado na base de alunos. Importe a lista de alunos primeiro.")

    st.text_input("Nome do Estudante", value=nome_estudante, key="nome_estudante")
    st.text_input("Telefone", value=telefone, key="telefone")
    turma = st.text_input("Turma")
    ano = st.text_input("Ano")
    data = st.date_input("Data")
    fatos = st.text_area("Descrição da Ocorrência")

    if st.button("Registrar Ocorrência"):
        if not cgm_input or not nome_estudante or not fatos:
            st.error("Preencha CGM, Nome do Estudante e descrição da ocorrência.")
        else:
            ocorrencia = {
                "CGM": cgm_input.strip(),
                "Nome do Estudante": nome_estudante,
                "Telefone": telefone,
                "Turma": turma,
                "Ano": ano,
                "Data": data.strftime("%Y-%m-%d"),
                "Fatos": fatos,
            }
            inserir_ocorrencia(conn, ocorrencia)
            st.success("Ocorrência registrada com sucesso!")
            st.experimental_rerun()

    st.subheader("Ocorrências registradas")
    df_ocorrencias = listar_ocorrencias(conn)
    if not df_ocorrencias.empty:
        st.dataframe(df_ocorrencias)
    else:
        st.info("Nenhuma ocorrência registrada ainda.")
