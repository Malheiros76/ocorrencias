import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from docx import Document

# Conexão com o banco de dados
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

# Criação das tabelas
c.execute('''
CREATE TABLE IF NOT EXISTS ocorrencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    cgm TEXT,
    nome_aluno TEXT,
    nome_responsavel TEXT,
    telefone_responsavel TEXT,
    turma TEXT,
    ano TEXT,
    fato TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS alunos (
    cgm TEXT PRIMARY KEY,
    nome_aluno TEXT,
    telefone TEXT
)
''')

conn.commit()

# Função para inserir ou atualizar aluno
def inserir_ou_atualizar_aluno(cgm, nome_aluno, telefone):
    c.execute('''
        INSERT OR REPLACE INTO alunos (cgm, nome_aluno, telefone)
        VALUES (?, ?, ?)
    ''', (cgm, nome_aluno, telefone))
    conn.commit()

# Interface Streamlit
st.title("Registro de Ocorrências Escolares")

# Definição das abas
aba = st.tabs(["Registrar Ocorrência", "Consultar por CGM", "Editar", "Excluir", "Importar Alunos", "Exportar"])

# ABA 1: Registrar Ocorrência
with aba[0]:
    st.subheader("Registrar nova ocorrência")

    data = st.date_input("Data da Ocorrência")
    cgm = st.text_input("CGM do Aluno")
    
    if "nome_aluno" not in st.session_state:
        st.session_state.nome_aluno = ""
        st.session_state.telefone = ""

    if cgm:
        aluno = c.execute("SELECT nome_aluno, telefone FROM alunos WHERE cgm = ?", (cgm,)).fetchone()
        if aluno:
            st.session_state.nome_aluno = aluno[0]
            st.session_state.telefone = aluno[1]

    nome_aluno = st.text_input("Nome do Aluno", value=st.session_state.nome_aluno)
    nome_responsavel = st.text_input("Nome do Responsável")
    telefone_responsavel = st.text_input("Telefone do Responsável", value=st.session_state.telefone)
    turma = st.text_input("Turma")
    ano = st.text_input("Ano")
    fato = st.text_area("Descreva o Fato")

    if st.button("Salvar Ocorrência"):
        c.execute('''INSERT INTO ocorrencias 
                     (data, cgm, nome_aluno, nome_responsavel, telefone_responsavel, turma, ano, fato) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (data.strftime("%Y-%m-%d"), cgm, nome_aluno, nome_responsavel, telefone_responsavel, turma, ano, fato))
        conn.commit()
        st.success("Ocorrência registrada com sucesso!")

# ABA 2: Consultar por CGM
with aba[1]:
    st.subheader("Consultar Ocorrências por CGM")

    cgm_consulta = st.text_input("Digite o CGM do aluno para consulta")

    if st.button("Consultar"):
        ocorrencias = c.execute("SELECT * FROM ocorrencias WHERE cgm = ?", (cgm_consulta,)).fetchall()
        if ocorrencias:
            df = pd.DataFrame(ocorrencias, columns=["ID", "Data", "CGM", "Aluno", "Responsável", "Telefone", "Turma", "Ano", "Fato"])
            st.dataframe(df)
        else:
            st.warning("Nenhuma ocorrência encontrada para este CGM.")

# ABA 3: Editar Ocorrência
with aba[2]:
    st.subheader("Editar Ocorrência")

    id_editar = st.number_input("ID da ocorrência a editar", min_value=1, step=1)

    if st.button("Carregar Dados"):
        ocorrencia = c.execute("SELECT * FROM ocorrencias WHERE id = ?", (id_editar,)).fetchone()
        if ocorrencia:
            _, data, cgm, nome_aluno, nome_responsavel, telefone_responsavel, turma, ano, fato = ocorrencia
            st.session_state.data = data
            st.session_state.cgm = cgm
            st.session_state.nome_aluno = nome_aluno
            st.session_state.nome_responsavel = nome_responsavel
            st.session_state.telefone_responsavel = telefone_responsavel
            st.session_state.turma = turma
            st.session_state.ano = ano
            st.session_state.fato = fato
        else:
            st.warning("ID não encontrado.")

    if "data" in st.session_state:
        data_nova = st.date_input("Data", value=pd.to_datetime(st.session_state.data))
        cgm_novo = st.text_input("CGM", value=st.session_state.cgm)
        nome_aluno_novo = st.text_input("Nome do Aluno", value=st.session_state.nome_aluno)
        nome_responsavel_novo = st.text_input("Responsável", value=st.session_state.nome_responsavel)
        telefone_responsavel_novo = st.text_input("Telefone", value=st.session_state.telefone_responsavel)
        turma_nova = st.text_input("Turma", value=st.session_state.turma)
        ano_novo = st.text_input("Ano", value=st.session_state.ano)
        fato_novo = st.text_area("Fato", value=st.session_state.fato)

        if st.button("Atualizar"):
            c.execute('''UPDATE ocorrencias SET 
                         data = ?, cgm = ?, nome_aluno = ?, nome_responsavel = ?, 
                         telefone_responsavel = ?, turma = ?, ano = ?, fato = ? 
                         WHERE id = ?''',
                      (data_nova.strftime("%Y-%m-%d"), cgm_novo, nome_aluno_novo, nome_responsavel_novo,
                       telefone_responsavel_novo, turma_nova, ano_novo, fato_novo, id_editar))
            conn.commit()
            st.success("Ocorrência atualizada com sucesso!")

# ABA 4: Excluir Ocorrência
with aba[3]:
    st.subheader("Excluir Ocorrência")

    id_excluir = st.number_input("ID da ocorrência a excluir", min_value=1, step=1)
    if st.button("Excluir"):
        c.execute("DELETE FROM ocorrencias WHERE id = ?", (id_excluir,))
        conn.commit()
        st.success("Ocorrência excluída com sucesso!")

# ABA 5: Importar Alunos
with aba[4]:
    st.subheader("Importar lista de alunos (.txt separado por tabulação)")

    uploaded_file = st.file_uploader("Selecione o arquivo .txt", type=["txt"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, sep="\t", encoding="utf-8")
        df.columns = [col.lower().strip().replace(" ", "_") for col in df.columns]
        
        for _, row in df.iterrows():
            inserir_ou_atualizar_aluno(
                cgm=str(row["cgm"]).strip(),
                nome_aluno=str(row["nome_do_estudante"]).strip(),
                telefone=str(row["telefone"]).strip() if "telefone" in row else "")

        st.success("Alunos importados com sucesso!")

# ABA 6: Exportar
with aba[5]:
    st.subheader("Exportar Ocorrências para .docx")

    ocorrencias = c.execute("SELECT * FROM ocorrencias").fetchall()
    if ocorrencias:
        doc = Document()
        doc.add_heading('Ocorrências Registradas', 0)
        for o in ocorrencias:
            doc.add_paragraph(f"ID: {o[0]}\nData: {o[1]}\nCGM: {o[2]}\nAluno: {o[3]}\nResponsável: {o[4]}\nTelefone: {o[5]}\nTurma: {o[6]}\nAno: {o[7]}\nFato: {o[8]}")
            doc.add_paragraph("-" * 50)

        output = BytesIO()
        doc.save(output)
        output.seek(0)

        st.download_button("Baixar Documento", output, file_name="ocorrencias.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.warning("Nenhuma ocorrência para exportar.")
