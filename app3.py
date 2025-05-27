import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from docx import Document
import base64

# Configuração da página
st.set_page_config(page_title="Registro de Ocorrências", layout="centered")

# Função para aplicar imagem de fundo com transparência de 50%
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
    background-position: 30%;
}}
.main .block-container {{
    background-color: rgba(255, 255, 255, 0.85);
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}}
</style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_background("Design_sem_nome-removebg-preview.png")

# Brasão no topo
doc_logo = "BRASÃO.png"
st.image(doc_logo, width=150)
st.markdown("## **Registro de Ocorrências – Colégio Cívico-Militar do Paraná**")
st.markdown("---")

# Conexão com banco de dados
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

# Cria tabela se não existir
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
    fatos TEXT
)
''')
conn.commit()

# Funções auxiliares
def inserir_ocorrencia(dados):
    c.execute('''INSERT INTO ocorrencias (cgm, nome_aluno, nome_responsavel, telefone_responsavel, turma, ano, data, fatos)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', dados)
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
    doc.add_picture(doc_logo, width=doc.sections[0].page_width * 0.2)
    doc.add_heading("Registro de Ocorrências", level=1)
    doc.add_paragraph(f"Nome do Aluno: {dados_aluno['nome_aluno']}")
    doc.add_paragraph(f"CGM: {dados_aluno['cgm']}")
    doc.add_paragraph(f"Turma: {dados_aluno['turma']} | Ano: {dados_aluno['ano']}")
    doc.add_paragraph("Fatos:")
    for _, row in registros.iterrows():
        doc.add_paragraph(f"{row['data']}: {row['fatos']}", style='Normal')
    nome_arquivo = f"Ocorrencias_{dados_aluno['nome_aluno'].replace(' ', '_')}.docx"
    doc.save(nome_arquivo)
    return nome_arquivo

# Interface de abas
aba = st.tabs(["📋 Registrar Ocorrência", "🔍 Consultar", "🛠️ Gerenciar", "📝 Exportar"])

with aba[0]:
    st.subheader("Registrar Ocorrência")

    if "limpar" not in st.session_state:
        st.session_state.limpar = False

    if st.button("🧹 Limpar"):
        st.session_state.limpar = True

    with st.form("registro_form"):
        cgm = st.text_input("CGM", value="" if st.session_state.limpar else "")
        nome_aluno = st.text_input("Nome do aluno", value="" if st.session_state.limpar else "")
        nome_responsavel = st.text_input("Nome do responsável", value="" if st.session_state.limpar else "")
        telefone_responsavel = st.text_input("Telefone do responsável", value="" if st.session_state.limpar else "")
        turma = st.text_input("Turma", value="" if st.session_state.limpar else "")
        ano = st.text_input("Ano", value="" if st.session_state.limpar else "")
        data = st.date_input("Data", value=datetime.today())
        fatos = st.text_area("Fatos ocorridos", value="" if st.session_state.limpar else "")

        submitted = st.form_submit_button("Salvar")

        if submitted:
            inserir_ocorrencia((
                cgm,
                nome_aluno,
                nome_responsavel,
                telefone_responsavel,
                turma,
                ano,
                data.strftime("%Y-%m-%d"),
                fatos
            ))
            st.success("Ocorrência registrada com sucesso!")
            st.session_state.limpar = True

    if st.session_state.limpar:
        st.session_state.limpar = False

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
                    if st.button("Salvar edição", key=f"save_{row['id']}"):
                        atualizar_ocorrencia(row['id'], 'fatos', novo_fato)
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
                    with open(nome_arquivo, "rb") as f:
                        st.download_button("Clique para baixar o DOCX", f, file_name=nome_arquivo)
            else:
                st.warning("Nenhuma ocorrência no período informado.")
