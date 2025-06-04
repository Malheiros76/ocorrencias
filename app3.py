import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- Conexão e criação das tabelas ---
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

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

# --- Inicializa session_state para campos ---
if "selected_cgm" not in st.session_state:
    st.session_state.selected_cgm = ""
if "selected_nome" not in st.session_state:
    st.session_state.selected_nome = ""
if "selected_telefone" not in st.session_state:
    st.session_state.selected_telefone = ""
if "aba_ativa" not in st.session_state:
    st.session_state.aba_ativa = 0

# Configuração página e layout
st.set_page_config(page_title="Registro de Ocorrências", layout="wide")

# Mostra o brasão (imagem na mesma pasta do app)
st.image("brasao.png", width=100)
st.title("Sistema de Registro de Ocorrências Escolares")

# --- Funções auxiliares ---
def buscar_ocorrencias(cgm):
    df = pd.read_sql_query("SELECT * FROM ocorrencias WHERE cgm = ?", conn, params=(cgm,))
    return df

def atualizar_ocorrencia(id_, campo, valor):
    c.execute(f"UPDATE ocorrencias SET {campo} = ? WHERE id = ?", (valor, id_))
    conn.commit()

def deletar_ocorrencia(id_):
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (id_,))
    conn.commit()

def limpar_campos_registro():
    st.session_state.selected_cgm = ""
    st.session_state.selected_nome = ""
    st.session_state.selected_telefone = ""
    st.session_state.cgm_registro = ""
    st.session_state.nome_registro = ""
    st.session_state.telefone_registro = ""
    st.session_state.turma_registro = ""
    st.session_state.ano_registro = ""
    st.session_state.data_ocorrencia_registro = date.today()
    st.session_state.fatos_registro = ""

def limpar_campos_consultar():
    st.session_state.cgm_busca = ""

def limpar_campos_editar():
    st.session_state.cgm_gestao = ""

def limpar_campos_exportar():
    st.session_state.cgm_export = ""
    st.session_state.data_ini = date.today()
    st.session_state.data_fim = date.today()

def limpar_campos_importar():
    # Não dá para limpar o file_uploader via session_state, então só faz nada aqui
    pass

def limpar_campos_lista_alunos():
    # Sem campos editáveis nessa aba
    pass

# --- Cria as abas ---
aba = st.tabs([
    "📋 Registrar Ocorrência",
    "🔍 Consultar Ocorrências",
    "✏️ Editar Ocorrência",
    "📄 Exportar Ocorrência",
    "📅 Importar Alunos",
    "📚 Lista de Alunos"
])

# --- Aba 0 - Registrar Ocorrência ---
with aba[0]:
    st.subheader("Registrar nova ocorrência")

    cgm = st.text_input("CGM do aluno", value=st.session_state.selected_cgm, key="cgm_registro")

    nome = ""
    telefone = ""
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
                c.execute("INSERT INTO ocorrencias (cgm, nome, telefone, turma, ano, data, fatos) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (cgm, nome_aluno, telefone_responsavel, turma, ano, data_ocorrencia.isoformat(), fatos))
                conn.commit()
                st.success("Ocorrência registrada com sucesso!")
                limpar_campos_registro()

    with col2:
        if st.button("Limpar"):
            limpar_campos_registro()

# --- Aba 1 - Consultar Ocorrências ---
def limpar_campos_consultar():
    st.session_state.cgm_busca = ""

with aba[1]:
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

# --- Aba 2 - Editar Ocorrência ---
with aba[2]:
    st.subheader("Gerenciar Ocorrências")
    cgm_gestao = st.text_input("CGM para editar/excluir", key="cgm_gestao")
    if st.button("Limpar", key="limpar_editar"):
        limpar_campos_editar()

    if cgm_gestao:
        resultados = buscar_ocorrencias(cgm_gestao)
        if not resultados.empty:
            for i, row in resultados.iterrows():
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

# --- Aba 3 - Exportar Ocorrência ---
with aba[3]:
    st.subheader("Exportar para .docx por período")

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
                # Aqui pode implementar exportação, por enquanto só mostra tabela
                st.dataframe(filtrado, use_container_width=True)
            else:
                st.warning("Nenhuma ocorrência no período informado.")

# --- Aba 4 - Importar Alunos ---
with aba[4]:
    st.subheader("Importar alunos via .txt")

    arquivo = st.file_uploader("Escolha o arquivo .txt com os dados dos alunos", type="txt")
    if st.button("Limpar", key="limpar_importar"):
        # Não é possível limpar file_uploader via código, então só mostra mensagem
        st.info("Para limpar o arquivo, remova manualmente no uploader.")

    if arquivo is not None:
        try:
            linhas = arquivo.read().decode("utf-8").splitlines()
            for linha in linhas[1:]:  # Pulando cabeçalho
                campos = linha.split("\t")
                if len(campos) >= 3:
                    cgm_arquivo = campos[0].strip()
                    nome_arquivo = campos[1].strip()
                    telefone_arquivo = campos[2].strip()
                    # Insere ou ignora se já existir
                    c.execute("INSERT OR IGNORE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", 
                              (cgm_arquivo, nome_arquivo, telefone_arquivo))
            conn.commit()
            st.success("Alunos importados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao importar arquivo: {e}")

# --- Aba 5 - Lista de Alunos ---
with aba[5]:
    st.subheader("Lista de alunos cadastrados")
    alunos_df = pd.read_sql_query("SELECT * FROM alunos", conn)
    st.dataframe(alunos_df, use_container_width=True)

