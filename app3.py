import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- Conexão com o banco ---
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

# --- Criação das tabelas ---
c.execute('''CREATE TABLE IF NOT EXISTS alunos (
    cgm TEXT PRIMARY KEY,
    nome TEXT,
    telefone TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS ocorrencias (
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

# --- Inicialização do session_state ---
for k in [
    "selected_cgm", "selected_nome", "selected_telefone", "aba_ativa",
    "cgm_registro", "nome_registro", "telefone_registro", "turma_registro",
    "ano_registro", "data_ocorrencia_registro", "fatos_registro",
    "cgm_busca", "cgm_gestao", "cgm_export", "data_ini", "data_fim"
]:
    if k not in st.session_state:
        st.session_state[k] = "" if "data" not in k else date.today()

# --- Configuração da página ---
st.set_page_config(page_title="Registro de Ocorrências", layout="wide")
st.image("brasao.png", width=100)
st.title("Sistema de Registro de Ocorrências Escolares")

# --- Funções auxiliares ---
def buscar_ocorrencias(cgm):
    return pd.read_sql_query("SELECT * FROM ocorrencias WHERE cgm = ?", conn, params=(cgm,))

def atualizar_ocorrencia(id_, campo, valor):
    c.execute(f"UPDATE ocorrencias SET {campo} = ? WHERE id = ?", (valor, id_))
    conn.commit()

def deletar_ocorrencia(id_):
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (id_,))
    conn.commit()

def limpar_campos_registro():
    for k in ["selected_cgm", "selected_nome", "selected_telefone", "cgm_registro",
              "nome_registro", "telefone_registro", "turma_registro", "ano_registro", "fatos_registro"]:
        st.session_state[k] = ""
    st.session_state.data_ocorrencia_registro = date.today()

def limpar_campos_consultar():
    st.session_state.cgm_busca = ""

def limpar_campos_editar():
    st.session_state.cgm_gestao = ""

def limpar_campos_exportar():
    st.session_state.cgm_export = ""
    st.session_state.data_ini = date.today()
    st.session_state.data_fim = date.today()

# --- Abas principais ---
abas = st.tabs([
    "📋 Registrar Ocorrência",
    "🔍 Consultar Ocorrências",
    "✏️ Editar Ocorrência",
    "📄 Exportar Ocorrência",
    "📅 Importar Alunos",
    "📚 Lista de Alunos"
])

# --- Aba 0: Registro ---
with abas[0]:
    st.subheader("Registrar nova ocorrência")
    cgm = st.text_input("CGM do aluno", value=st.session_state.selected_cgm, key="cgm_registro")

    nome, telefone = "", ""
    if cgm:
        aluno = c.execute("SELECT nome, telefone FROM alunos WHERE cgm = ?", (cgm,)).fetchone()
        if aluno:
            nome, telefone = aluno

    if st.session_state.selected_nome:
        nome = st.session_state.selected_nome
    if st.session_state.selected_telefone:
        telefone = st.session_state.selected_telefone

    nome_aluno = st.text_input("Nome do aluno", value=nome, key="nome_registro")
    telefone_responsavel = st.text_input("Telefone do responsável", value=telefone, key="telefone_registro")
    turma = st.text_input("Turma", key="turma_registro")
    ano = st.text_input("Ano", key="ano_registro")
    data_ocorrencia = st.date_input("Data da ocorrência", value=date.today(), key="data_ocorrencia_registro")
    fatos = st.text_area("Fatos ocorridos", key="fatos_registro")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Registrar"):
            if not cgm or not nome_aluno:
                st.error("Preencha pelo menos CGM e nome do aluno.")
            else:
                c.execute("""
                    INSERT INTO ocorrencias (cgm, nome, telefone, turma, ano, data, fatos)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (cgm, nome_aluno, telefone_responsavel, turma, ano, data_ocorrencia.isoformat(), fatos))
                conn.commit()
                st.success("Ocorrência registrada com sucesso!")
                limpar_campos_registro()

    with col2:
        if st.button("Limpar"):
            limpar_campos_registro()

# --- Aba 1: Consulta ---
with abas[1]:
    st.subheader("Consultar ocorrências")
    cgm_busca = st.text_input("Digite o CGM para buscar ocorrências", key="cgm_busca")
    st.button("Limpar", key="limpar_consultar", on_click=limpar_campos_consultar)
    
    if cgm_busca:
        ocorrencias = c.execute("SELECT data, fatos FROM ocorrencias WHERE cgm = ? ORDER BY data DESC", (cgm_busca,)).fetchall()
        if ocorrencias:
            df = pd.DataFrame(ocorrencias, columns=["Data", "Fatos"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma ocorrência encontrada para este CGM.")

# --- Aba 2: Edição/Exclusão ---
with abas[2]:
    st.subheader("Gerenciar Ocorrências")
    cgm_gestao = st.text_input("CGM para editar/excluir", key="cgm_gestao")
    if st.button("Limpar", key="limpar_editar"):
        limpar_campos_editar()

    if cgm_gestao:
        resultados = buscar_ocorrencias(cgm_gestao)
        if not resultados.empty:
            for _, row in resultados.iterrows():
                with st.expander(f"{row['data']} - {row['fatos'][:30]}..."):
                    novo_fato = st.text_area("Editar fatos", row['fatos'], key=f"edit_{row['id']}")
                    novo_aplicador = st.text_input("Editar Agente Aplicador", row.get('agente_aplicador', ""), key=f"aplicador_{row['id']}")
                    if st.button("Salvar edição", key=f"save_{row['id']}"):
                        atualizar_ocorrencia(row['id'], 'fatos', novo_fato)
                        atualizar_ocorrencia(row['id'], 'agente_aplicador', novo_aplicador)
                        st.success("Atualizado!")
                    if st.button("🔚 Excluir", key=f"delete_{row['id']}"):
                        deletar_ocorrencia(row['id'])
                        st.warning("Excluído!")

# --- Aba 3: Exportação ---
with abas[3]:
    st.subheader("Exportar ocorrências por período")

    cgm_export = st.text_input("CGM para exportar", key="cgm_export")
    data_ini = st.date_input("Data inicial", value=date.today(), key="data_ini")
    data_fim = st.date_input("Data final", value=date.today(), key="data_fim")

    if st.button("Limpar", key="limpar_exportar"):
        limpar_campos_exportar()

    if cgm_export:
        dados = buscar_ocorrencias(cgm_export)
        if not dados.empty:
            dados["data"] = pd.to_datetime(dados["data"])
            filtrado = dados[(dados["data"] >= pd.to_datetime(data_ini)) & (dados["data"] <= pd.to_datetime(data_fim))]
            if not filtrado.empty:
                st.write(f"{len(filtrado)} ocorrências encontradas no período.")
                st.dataframe(filtrado, use_container_width=True)
                # Aqui você pode implementar exportação para PDF/Word
            else:
                st.warning("Nenhuma ocorrência no período informado.")

# --- Aba 4: Importação ---
with abas[4]:
    st.subheader("Importar alunos via .txt")
    arquivo = st.file_uploader("Escolha o arquivo .txt com os dados dos alunos", type="txt")

    if st.button("Limpar", key="limpar_importar"):
        st.info("Para limpar o arquivo, remova manualmente no uploader.")

    if arquivo is not None:
        try:
            linhas = arquivo.read().decode("utf-8").splitlines()
            for linha in linhas[1:]:  # Pula cabeçalho
                campos = linha.split("\t")
                if len(campos) >= 3:
                    cgm_arquivo = campos[0].strip()
                    nome_arquivo = campos[1].strip()
                    telefone_arquivo = campos[2].strip()
                    c.execute("INSERT OR IGNORE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", 
                              (cgm_arquivo, nome_arquivo, telefone_arquivo))
            conn.commit()
            st.success("Alunos importados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao importar arquivo: {e}")

# --- Aba 5: Lista de alunos ---
with abas[5]:
    st.subheader("Lista de alunos cadastrados")
    alunos_df = pd.read_sql_query("SELECT * FROM alunos", conn)
    st.dataframe(alunos_df, use_container_width=True)
