import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from docx import Document
import base64
import os

st.set_page_config(page_title="Registro de Ocorrências", layout="centered")

def set_background(png_file):
    with open(png_file, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.5)),
                    url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.85);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }}
    label, .stTextInput label, .stTextArea label, .stDateInput label {{
        color: #666666 !important;
        font-weight: bold;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: black !important;
        font-weight: bold;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_background("Design_sem_nome-removebg-preview.png")

st.image("BRASÃO.png", width=150)
st.markdown("## **Registro de Ocorrências – Colégio Cívico-Militar do Paraná**")
st.markdown("---")

# Banco de dados
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

# Criação tabela ocorrencias
c.execute('''
CREATE TABLE IF NOT EXISTS ocorrencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cgm TEXT,
    nome_aluno TEXT,
    nome_responsavel TEXT,
    telefone_responsavel TEXT,
    turma TEXT,
    ano TEXT,
    data TEXT,
    fatos TEXT,
    agente_aplicador TEXT
)
''')

# Criação tabela alunos
c.execute('''
CREATE TABLE IF NOT EXISTS alunos (
    cgm TEXT PRIMARY KEY,
    nome TEXT,
    nascimento TEXT,
    idade INTEGER,
    sexo TEXT,
    telefone TEXT,
    rg TEXT,
    situacao TEXT,
    data_matricula TEXT,
    turma TEXT
)
''')

conn.commit()

def inserir_ocorrencia(dados):
    c.execute('''INSERT INTO ocorrencias (
        cgm, nome_aluno, nome_responsavel, telefone_responsavel,
        turma, ano, data, fatos, agente_aplicador
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', dados)
    conn.commit()

def buscar_ocorrencias(cgm):
    return pd.read_sql_query("SELECT * FROM ocorrencias WHERE cgm = ? ORDER BY data DESC", conn, params=(cgm,))

def deletar_ocorrencia(id):
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (id,))
    conn.commit()

def atualizar_ocorrencia(id, coluna, valor):
    c.execute(f"UPDATE ocorrencias SET {coluna} = ? WHERE id = ?", (valor, id))
    conn.commit()

def exportar_para_docx(dados_aluno, registros):
    doc = Document()
    if os.path.exists("BRASÃO.png"):
        doc.add_picture("BRASÃO.png", width=doc.sections[0].page_width * 0.2)
    doc.add_heading("COLÉGIO CÍVICO-MILITAR DO PARANÁ", level=1)
    doc.add_heading("REGISTRO DE OCORRÊNCIA DISCIPLINAR", level=2)
    doc.add_paragraph(f"Aluno: {dados_aluno['nome_aluno']}")
    doc.add_paragraph(f"CGM: {dados_aluno['cgm']} | Turma: {dados_aluno['turma']} | Ano: {dados_aluno['ano']}")
    doc.add_paragraph("")
    doc.add_paragraph("FATOS REGISTRADOS:")
    for _, row in registros.iterrows():
        agente = row.get("agente_aplicador", "N/A") or "N/A"
        doc.add_paragraph(f"{row['data']} - {agente}: {row['fatos']}", style='Normal')
    nome_arquivo = f"Ocorrencias_{dados_aluno['nome_aluno'].replace(' ', '_')}.docx"
    doc.save(nome_arquivo)
    return nome_arquivo

# Funções para alunos
def inserir_ou_atualizar_aluno(dados_aluno):
    c.execute('''
    INSERT INTO alunos (cgm, nome, nascimento, idade, sexo, telefone, rg, situacao, data_matricula, turma)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(cgm) DO UPDATE SET
        nome=excluded.nome,
        nascimento=excluded.nascimento,
        idade=excluded.idade,
        sexo=excluded.sexo,
        telefone=excluded.telefone,
        rg=excluded.rg,
        situacao=excluded.situacao,
        data_matricula=excluded.data_matricula,
        turma=excluded.turma
    ''', dados_aluno)
    conn.commit()

def buscar_aluno_por_cgm(cgm):
    c.execute("SELECT * FROM alunos WHERE cgm = ?", (cgm,))
    return c.fetchone()

# Abas
aba = st.tabs([
    "📋 Registrar Ocorrência", 
    "🔍 Consultar", 
    "🛠️ Gerenciar", 
    "📝 Exportar",
    "📥 Importar Alunos"
])

with aba[0]:
    st.subheader("Registrar Ocorrência")

    for campo in ["cgm", "nome_aluno", "nome_responsavel", "telefone_responsavel",
                  "turma", "ano", "agente_aplicador", "fatos"]:
        if campo not in st.session_state:
            st.session_state[campo] = ""

    # Auto preencher ao digitar CGM
    if st.session_state.get("cgm"):
        aluno = buscar_aluno_por_cgm(st.session_state["cgm"])
        if aluno:
            st.session_state["nome_aluno"] = aluno[1]
            st.session_state["telefone_responsavel"] = aluno[5]
            st.session_state["turma"] = aluno[9]

    if st.button("🧹 Limpar"):
        for campo in ["cgm", "nome_aluno", "nome_responsavel", "telefone_responsavel",
                      "turma", "ano", "agente_aplicador", "fatos"]:
            st.session_state[campo] = ""

    with st.form("registro_form"):
        st.session_state["cgm"] = st.text_input("CGM", value=st.session_state["cgm"])
        st.session_state["nome_aluno"] = st.text_input("Nome do aluno", value=st.session_state["nome_aluno"])
        st.session_state["nome_responsavel"] = st.text_input("Nome do responsável", value=st.session_state["nome_responsavel"])
        st.session_state["telefone_responsavel"] = st.text_input("Telefone do responsável", value=st.session_state["telefone_responsavel"])
        st.session_state["turma"] = st.text_input("Turma", value=st.session_state["turma"])
        st.session_state["ano"] = st.text_input("Ano", value=st.session_state["ano"])
        st.session_state["agente_aplicador"] = st.text_input("Agente Aplicador", value=st.session_state["agente_aplicador"])
        data = st.date_input("Data", value=datetime.today())
        st.session_state["fatos"] = st.text_area("Fatos ocorridos", value=st.session_state["fatos"])

        if st.form_submit_button("Salvar"):
            inserir_ocorrencia((
                st.session_state["cgm"],
                st.session_state["nome_aluno"],
                st.session_state["nome_responsavel"],
                st.session_state["telefone_responsavel"],
                st.session_state["turma"],
                st.session_state["ano"],
                data.strftime("%Y-%m-%d"),
                st.session_state["fatos"],
                st.session_state["agente_aplicador"]
            ))
            st.success("Ocorrência registrada com sucesso!")
            for campo in ["cgm", "nome_aluno", "nome_responsavel", "telefone_responsavel",
                          "turma", "ano", "agente_aplicador", "fatos"]:
                st.session_state[campo] = ""

with aba[1]:
    st.subheader("Consultar por CGM")
    cgm_consulta = st.text_input("Digite o CGM do aluno para consultar")
    if cgm_consulta:
        resultados = buscar_ocorrencias(cgm_consulta)
        if not resultados.empty:
            st.dataframe(resultados)
        else:
            st.warning("Nenhuma ocorrência encontrada.")

with aba[2]:
    st.subheader("Gerenciar Ocorrências")
    cgm_gestao = st.text_input("CGM para editar/excluir")
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
                    if st.button("🗑️ Excluir", key=f"delete_{row['id']}"):
                        deletar_ocorrencia(row['id'])
                        st.warning("Excluído!")

with aba[3]:
    st.subheader("Exportar para .docx por período")
    cgm_export = st.text_input("CGM para exportar")
    col1, col2 = st.columns(2)
    with col1:
        data_ini = st.date_input("Data inicial", value=datetime.today())
    with col2:
        data_fim = st.date_input("Data final", value=datetime.today())
    if cgm_export:
        dados = buscar_ocorrencias(cgm_export)
        if not dados.empty:
            dados["data"] = pd.to_datetime(dados["data"])
            filtrado = dados[(dados["data"] >= pd.to_datetime(data_ini)) & (dados["data"] <= pd.to_datetime(data_fim))]
            if not filtrado.empty:
                if st.button("📄 Exportar para Word"):
                    nome_arquivo = exportar_para_docx(filtrado.iloc[0], filtrado)
                    with open(nome_arquivo)
with aba[4]:
    st.subheader("Importar Alunos via arquivo .txt")

    uploaded_file = st.file_uploader("Escolha o arquivo .txt com os dados dos alunos", type=["txt"])
    if uploaded_file is not None:
        # Lê o arquivo txt em um DataFrame assumindo que seja tabulado por tabulação
        try:
            df = pd.read_csv(uploaded_file, sep="\t")
            st.success("Arquivo carregado com sucesso!")
            st.dataframe(df.head())

            # Botão para importar os dados para a tabela alunos
            if st.button("Importar dados para o banco"):
                erros = 0
                for _, row in df.iterrows():
                    try:
                        dados_aluno = (
                            str(row["CGM"]).strip(),
                            str(row["Nome do Estudante"]).strip(),
                            str(row.get("Nascimento", "")).strip(),
                            int(row.get("Idade", 0)),
                            str(row.get("Sexo", "")).strip(),
                            str(row.get("Telefone", "")).strip(),
                            str(row.get("RG", "")).strip(),
                            str(row.get("Situação", "")).strip(),
                            str(row.get("Data de Matrícula", "")).strip(),
                            str(row.get("Turma", "")).strip()
                        )
                        inserir_ou_atualizar_aluno(dados_aluno)
                    except Exception as e:
                        erros += 1
                        st.error(f"Erro na linha {_}: {e}")

                if erros == 0:
                    st.success("Todos os alunos foram importados com sucesso!")
                else:
                    st.warning(f"Importação concluída com {erros} erros.")

        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
