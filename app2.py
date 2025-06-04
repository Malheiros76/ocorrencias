import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64

st.set_page_config(page_title="Registro de Ocorrências", layout="wide")

# --- Banco de dados ---
def get_connection():
    conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
    return conn

def criar_tabelas(conn):
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS alunos (
        cgm TEXT PRIMARY KEY,
        nome TEXT,
        telefone TEXT
    )''')

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
        agente_aplicador TEXT
    )''')
    conn.commit()

# --- Funções auxiliares ---
def buscar_ocorrencias(conn, cgm):
    return pd.read_sql_query("SELECT * FROM ocorrencias WHERE cgm = ?", conn, params=(cgm,))

def atualizar_ocorrencia(conn, id_, campo, valor):
    c = conn.cursor()
    c.execute(f"UPDATE ocorrencias SET {campo} = ? WHERE id = ?", (valor, id_))
    conn.commit()

def deletar_ocorrencia(conn, id_):
    c = conn.cursor()
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (id_,))
    conn.commit()

def inserir_ocorrencia(conn, cgm, nome, telefone, turma, ano, data, fatos, agente_aplicador=""):
    c = conn.cursor()
    c.execute('''
        INSERT INTO ocorrencias (cgm, nome, telefone, turma, ano, data, fatos, agente_aplicador)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (cgm, nome, telefone, turma, ano, data, fatos, agente_aplicador))
    conn.commit()

def buscar_alunos(conn):
    return pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)

def importar_alunos(conn, df):
    c = conn.cursor()
    inseridos = 0
    for _, row in df.iterrows():
        c.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)",
                  (row["cgm"], row["nome"], row["telefone"]))
        inseridos += 1
    conn.commit()
    return inseridos

# --- Interface de cada aba ---
def aba_registrar_ocorrencia(conn):
    st.subheader("Registrar nova ocorrência")
    with st.form("form_ocorrencia"):
        cgm = st.text_input("CGM do aluno", value=st.session_state.get("selected_cgm", ""))
        nome = st.text_input("Nome do aluno", value=st.session_state.get("selected_nome", ""))
        telefone = st.text_input("Telefone do responsável", value=st.session_state.get("selected_telefone", ""))
        turma = st.text_input("Turma")
        ano = st.text_input("Ano")
        data_ocorrencia = st.date_input("Data da ocorrência", value=date.today())
        fatos = st.text_area("Fatos ocorridos")
        agente_aplicador = st.text_input("Agente aplicador")

        if st.form_submit_button("Registrar"):
            if not cgm or not nome:
                st.error("Preencha pelo menos CGM e Nome para registrar.")
            else:
                inserir_ocorrencia(conn, cgm, nome, telefone, turma, ano, data_ocorrencia.isoformat(), fatos, agente_aplicador)
                st.success("Ocorrência registrada com sucesso!")
                # Limpa seleção
                st.session_state.selected_cgm = ""
                st.session_state.selected_nome = ""
                st.session_state.selected_telefone = ""
                st.experimental_rerun()

def aba_consultar_ocorrencias(conn):
    st.subheader("Consultar ocorrências")
    cgm_consulta = st.text_input("CGM do aluno para consulta")
    if cgm_consulta:
        dados = buscar_ocorrencias(conn, cgm_consulta)
        if not dados.empty:
            df = dados[["data", "fatos"]].sort_values(by="data", ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma ocorrência encontrada.")

def aba_editar_ocorrencias(conn):
    st.subheader("Editar/Excluir Ocorrências")
    cgm_edicao = st.text_input("CGM para editar")
    if cgm_edicao:
        ocorrencias = buscar_ocorrencias(conn, cgm_edicao)
        if not ocorrencias.empty:
            for _, row in ocorrencias.iterrows():
                with st.expander(f"{row['data']} - {row['fatos'][:30]}..."):
                    novo_fato = st.text_area("Fatos", row["fatos"], key=f"fato_{row['id']}")
                    novo_aplicador = st.text_input("Agente aplicador", row.get("agente_aplicador", ""), key=f"agente_{row['id']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Salvar", key=f"salvar_{row['id']}"):
                            atualizar_ocorrencia(conn, row['id'], "fatos", novo_fato)
                            atualizar_ocorrencia(conn, row['id'], "agente_aplicador", novo_aplicador)
                            st.success("Atualizado com sucesso!")
                    with col2:
                        if st.button("Excluir", key=f"excluir_{row['id']}"):
                            deletar_ocorrencia(conn, row['id'])
                            st.warning("Ocorrência excluída.")

def aba_importar_alunos(conn):
    st.subheader("Importar alunos (.txt)")
    arquivo = st.file_uploader("Arquivo .txt com colunas CGM, Nome do Estudante, Telefone", type="txt")

    if arquivo:
        try:
            df = pd.read_csv(arquivo, sep="\t", engine="python")
            df.columns = [col.strip() for col in df.columns]
            if all(col in df.columns for col in ["CGM", "Nome do Estudante", "Telefone"]):
                df = df.rename(columns={
                    "CGM": "cgm",
                    "Nome do Estudante": "nome",
                    "Telefone": "telefone"
                })
                inseridos = importar_alunos(conn, df)
                st.success(f"{inseridos} alunos importados com sucesso!")
                st.dataframe(df)
            else:
                st.error("Formato incorreto. Verifique as colunas do .txt.")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

def aba_lista_alunos(conn):
    st.subheader("Lista de alunos")
    alunos = buscar_alunos(conn)
    
    for _, row in alunos.iterrows():
        checked = st.checkbox(f"{row['cgm']} - {row['nome']}", key=f"chk_{row['cgm']}")
        if checked:
            st.session_state.selected_cgm = row['cgm']
            st.session_state.selected_nome = row['nome']
            st.session_state.selected_telefone = row['telefone']
            st.experimental_rerun()

# --- Main ---

def main():
    conn = get_connection()
    criar_tabelas(conn)

    if "selected_cgm" not in st.session_state:
        st.session_state.selected_cgm = ""
    if "selected_nome" not in st.session_state:
        st.session_state.selected_nome = ""
    if "selected_telefone" not in st.session_state:
        st.session_state.selected_telefone = ""

    abas = st.tabs([
        "📋 Registrar Ocorrência",
        "🔍 Consultar Ocorrências",
        "✏️ Editar Ocorrência",
        "📥 Importar Alunos",
        "📚 Lista de Alunos"
    ])

    aba_registrar_ocorrencia(conn)
    with abas[1]:
        aba_consultar_ocorrencias(conn)
    with abas[2]:
        aba_editar_ocorrencias(conn)
    with abas[3]:
        aba_importar_alunos(conn)
    with abas[4]:
        aba_lista_alunos(conn)

if __name__ == "__main__":
    main()
