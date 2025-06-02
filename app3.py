import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64

# Configuração da página
st.set_page_config(page_title="Registro de Ocorrências", layout="wide")

# Função para definir papel de parede
def set_background(image_file):
    try:
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
    except FileNotFoundError:
        st.warning("Imagem de fundo não encontrada.")

set_background("fundo.png")  # Ajuste o caminho se precisar

# Exibir brasão
try:
    st.image("brasao.png", width=200)
except FileNotFoundError:
    st.warning("Imagem do brasão não encontrada.")

# Conexão com banco SQLite
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

# Criar tabelas
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
    agente_aplicador TEXT
)
''')
conn.commit()

# Estado inicial da sessão
if "selected_cgm" not in st.session_state:
    st.session_state.selected_cgm = ""
if "selected_nome" not in st.session_state:
    st.session_state.selected_nome = ""
if "selected_telefone" not in st.session_state:
    st.session_state.selected_telefone = ""
if "cgms_importados" not in st.session_state:
    # Carregar CGMs do banco para a sessão
    c.execute("SELECT cgm FROM alunos")
    st.session_state.cgms_importados = [row[0] for row in c.fetchall()]

# Funções auxiliares
def buscar_ocorrencias(cgm):
    return pd.read_sql_query("SELECT * FROM ocorrencias WHERE cgm = ?", conn, params=(cgm,))

def buscar_aluno_por_cgm(cgm):
    c.execute("SELECT nome, telefone FROM alunos WHERE cgm = ?", (cgm,))
    res = c.fetchone()
    if res:
        return {"nome": res[0], "telefone": res[1]}
    return None

def atualizar_ocorrencia(id_, campo, valor):
    c.execute(f"UPDATE ocorrencias SET {campo} = ? WHERE id = ?", (valor, id_))
    conn.commit()

def deletar_ocorrencia(id_):
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (id_,))
    conn.commit()

def exportar_para_docx(primeira_linha, df):
    # Implementação simples placeholder
    nome_arquivo = "ocorrencias.docx"
    # Você pode implementar exportação real aqui
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("Relatório de Ocorrências\n\n")
        for idx, row in df.iterrows():
            f.write(f"Data: {row['data'].strftime('%Y-%m-%d')}\n")
            f.write(f"Fatos: {row['fatos']}\n\n")
    return nome_arquivo

# Interface: abas
abas = st.tabs([
    "📋 Registrar Ocorrência",
    "🔍 Consultar Ocorrências",
    "✏️ Editar Ocorrência",
    "📄 Exportar Ocorrência",
    "📥 Importar Alunos",
    "📚 Lista de Alunos"
])

# ========== ABA 0 - Registrar Ocorrência ==========
with abas[0]:
    st.subheader("Registrar nova ocorrência")

    # Carregar CGMs para selectbox
    cgms_disponiveis = st.session_state.get("cgms_importados", [])

    cgm_manual = st.text_input("Digite CGM do aluno manualmente:", value=st.session_state.selected_cgm)
    cgm_select = st.selectbox("Ou selecione CGM importado:", options=[""] + cgms_disponiveis, index=0)
    cgm_final = cgm_manual.strip() if cgm_manual.strip() else cgm_select

    aluno_info = buscar_aluno_por_cgm(cgm_final) if cgm_final else None

    nome_val = aluno_info["nome"] if aluno_info else st.session_state.selected_nome
    telefone_val = aluno_info["telefone"] if aluno_info else st.session_state.selected_telefone

    with st.form("form_ocorrencia"):
        cgm = st.text_input("CGM do aluno", value=cgm_final, key="form_cgm")
        nome = st.text_input("Nome do aluno", value=nome_val, key="form_nome")
        telefone = st.text_input("Telefone do responsável", value=telefone_val, key="form_telefone")
        turma = st.text_input("Turma")
        ano = st.text_input("Ano")
        data_ocorrencia = st.date_input("Data da ocorrência", value=date.today())
        fatos = st.text_area("Fatos ocorridos")
        agente_aplicador = st.text_input("Agente aplicador")

        if st.form_submit_button("Registrar"):
            # Validações básicas
            if not cgm or not nome or not telefone or not agente_aplicador:
                st.error("Por favor, preencha todos os campos obrigatórios (CGM, Nome, Telefone, Agente aplicador).")
            else:
                c.execute('''
                    INSERT INTO ocorrencias (cgm, nome, telefone, turma, ano, data, fatos, agente_aplicador)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (cgm, nome, telefone, turma, ano, data_ocorrencia.isoformat(), fatos, agente_aplicador))
                conn.commit()
                st.success("Ocorrência registrada com sucesso!")

# ========== ABA 1 - Consultar Ocorrências ==========
with abas[1]:
    st.subheader("Consultar ocorrências")
    cgm_consulta = st.text_input("CGM do aluno para consulta")
    if cgm_consulta:
        dados = buscar_ocorrencias(cgm_consulta.strip())
        if not dados.empty:
            df = dados[["data", "fatos"]].sort_values(by="data", ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma ocorrência encontrada.")

# ========== ABA 2 - Editar/Excluir Ocorrências ==========
with abas[2]:
    st.subheader("Editar/Excluir Ocorrências")
    cgm_edicao = st.text_input("CGM para editar")
    if cgm_edicao:
        ocorrencias = buscar_ocorrencias(cgm_edicao.strip())
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

# ==
