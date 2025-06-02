import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64

# ✅ ESTA LINHA DEVE SER A PRIMEIRA COMANDO DO STREAMLIT
st.set_page_config(page_title="Registro de Ocorrências", layout="wide")

# Definir papel de parede
def set_background(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("fundo.png")  # Certifique-se de que o arquivo está na mesma pasta
# Defenir Brasao
st.image("brasao.png", width=200)

# Conexão com banco de dados SQLite
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

# Criação das tabelas
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

# Estado inicial
if "selected_cgm" not in st.session_state:
    st.session_state.selected_cgm = ""
if "selected_nome" not in st.session_state:
    st.session_state.selected_nome = ""
if "selected_telefone" not in st.session_state:
    st.session_state.selected_telefone = ""

# Abas
abas = st.tabs([
    "📋 Registrar Ocorrência",
    "🔍 Consultar Ocorrências",
    "✏️ Editar Ocorrência",
    "📄 Exportar Ocorrência",
    "📥 Importar Alunos",
    "📚 Lista de Alunos"
])

# Funções
def buscar_ocorrencias(cgm):
    return pd.read_sql_query("SELECT * FROM ocorrencias WHERE cgm = ?", conn, params=(cgm,))

def atualizar_ocorrencia(id_, campo, valor):
    c.execute(f"UPDATE ocorrencias SET {campo} = ? WHERE id = ?", (valor, id_))
    conn.commit()

def deletar_ocorrencia(id_):
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (id_,))
    conn.commit()

def exportar_para_docx(primeira_linha, df):
    # Aqui você pode implementar exportação real com python-docx se quiser
    nome_arquivo = "ocorrencias.docx"
    return nome_arquivo

# Aba 0 - Registro
with abas[0]:
    st.subheader("Registrar nova ocorrência")
    with st.form("form_ocorrencia"):
        cgm = st.text_input("CGM do aluno", value=st.session_state.selected_cgm)
        nome = st.text_input("Nome do aluno", value=st.session_state.selected_nome)
        telefone = st.text_input("Telefone do responsável", value=st.session_state.selected_telefone)
        turma = st.text_input("Turma")
        ano = st.text_input("Ano")
        data_ocorrencia = st.date_input("Data da ocorrência", value=date.today())
        fatos = st.text_area("Fatos ocorridos")
        agente_aplicador = st.text_input("Nome do agente aplicador")

        if st.form_submit_button("Registrar"):
            if not agente_aplicador.strip():
                st.error("Por favor, preencha o nome do agente aplicador.")
            else:
                c.execute('''INSERT INTO ocorrencias (cgm, nome, telefone, turma, ano, data, fatos, agente_aplicador)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (cgm, nome, telefone, turma, ano, data_ocorrencia.isoformat(), fatos, agente_aplicador))
                conn.commit()
                st.success("Ocorrência registrada com sucesso!")

# Aba 1 - Consulta
with abas[1]:
    st.subheader("Consultar ocorrências")
    cgm_consulta = st.text_input("CGM do aluno para consulta")
    if cgm_consulta:
        dados = buscar_ocorrencias(cgm_consulta)
        if not dados.empty:
            df = dados[["data", "fatos"]].sort_values(by="data", ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma ocorrência encontrada.")

# Aba 2 - Editar
with abas[2]:
    st.subheader("Editar/Excluir Ocorrências")
    cgm_edicao = st.text_input("CGM para editar")
    if cgm_edicao:
        ocorrencias = buscar_ocorrencias(cgm_edicao)
        if not ocorrencias.empty:
            for _, row in ocorrencias.iterrows():
                with st.expander(f"{row['data']} - {row['fatos'][:30]}..."):
                    novo_fato = st.text_area("Fatos", row["fatos"], key=f"fato_{row['id']}")
                    novo_aplicador = st.text_input("Agente aplicador", row.get("agente_aplicador", ""), key=f"agente_{row['id']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Salvar", key=f"salvar_{row['id']}"):
                            atualizar_ocorrencia(row['id'], "fatos", novo_fato)
                            atualizar_ocorrencia(row['id'], "agente_aplicador", novo_aplicador)
                            st.success("Atualizado com sucesso!")
                    with col2:
                        if st.button("Excluir", key=f"excluir_{row['id']}"):
                            deletar_ocorrencia(row['id'])
                            st.warning("Ocorrência excluída.")

# Aba 3 - Exportar
with abas[3]:
    st.subheader("Exportar para Word (.docx)")
    cgm_exportar = st.text_input("CGM para exportar")
    col1, col2 = st.columns(2)
    with col1:
        data_ini = st.date_input("Data inicial", value=date.today())
    with col2:
        data_fim = st.date_input("Data final", value=date.today())

    if cgm_exportar:
        df = buscar_ocorrencias(cgm_exportar)
        df["data"] = pd.to_datetime(df["data"])
        df_filtrado = df[(df["data"] >= pd.to_datetime(data_ini)) & (df["data"] <= pd.to_datetime(data_fim))]
        if not df_filtrado.empty and st.button("Exportar"):
            arquivo = exportar_para_docx(df_filtrado.iloc[0], df_filtrado)
            with open(arquivo, "rb") as f:
                st.download_button("📥 Baixar DOCX", f, file_name=arquivo)
        elif df_filtrado.empty:
            st.warning("Nenhuma ocorrência neste período.")

# Aba 4 - Importar
with abas[4]:
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
                inseridos = 0
                for _, row in df.iterrows():
                    c.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)",
                              (row["cgm"], row["nome"], row["telefone"]))
                    inseridos += 1
                conn.commit()
                st.success(f"{inseridos} alunos importados com sucesso!")
                st.dataframe(df)
            else:
                st.error("Formato incorreto. Verifique as colunas do .txt.")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

# Aba 5 - Lista de Alunos
with abas[5]:
    st.subheader("Lista de alunos")
    alunos = pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)
    for _, row in alunos.iterrows():
        if st.button(f"{row['cgm']} - {row['nome']}", key=row['cgm']):
            st.session_state.selected_cgm = row['cgm']
            st.session_state.selected_nome = row['nome']
            st.session_state.selected_telefone = row['telefone']
            st.experimental_rerun()
