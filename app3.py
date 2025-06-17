import streamlit as st
import sqlite3
from datetime import datetime
from docx import Document
from docx.shared import Inches
from fpdf import FPDF
import os

# Função conexão
def conectar():
    return sqlite3.connect('ocorrencias.db')

# Criar tabelas
def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ocorrencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cgm TEXT,
        nome TEXT,
        data TEXT,
        descricao TEXT
    )
    """)

    conn.commit()
    conn.close()

# Registro de ocorrência
def registrar_ocorrencia():
    st.title("Registro de Ocorrências")

    cgm = st.text_input("CGM")
    nome = st.text_input("Nome do Aluno")
    descricao = st.text_area("Descrição da Ocorrência")

    if st.button("Salvar Ocorrência"):
        data = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ocorrencias (cgm, nome, data, descricao)
            VALUES (?, ?, ?, ?)
        """, (cgm, nome, data, descricao))
        conn.commit()
        conn.close()
        st.success("Ocorrência registrada!")

# Exportar Word
def exportar_para_word(resultados):
    doc = Document()

    # Cabeçalho com imagem
    if os.path.exists("CABEÇARIOAPP.png"):
        doc.add_picture("CABEÇARIOAPP.png", width=Inches(6))

    doc.add_heading("Relatório de Ocorrências", level=1)

    for cgm, nome, data, desc in resultados:
        doc.add_paragraph(f"CGM: {cgm}\nNome: {nome}\nData: {data}\nDescrição: {desc}\n-------------------------")

    arquivo_word = "relatorio_ocorrencias.docx"
    doc.save(arquivo_word)
    return arquivo_word

# Exportar PDF
def exportar_para_pdf(resultados):
    pdf = FPDF()
    pdf.add_page()

    # Cabeçalho com imagem
    if os.path.exists("CABEÇARIOAPP.png"):
        pdf.image("CABEÇARIOAPP.png", x=10, y=8, w=pdf.w - 20)
        pdf.ln(50)  # Espaço depois da imagem
    else:
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Relatório de Ocorrências", ln=True, align='C')

    pdf.set_font("Arial", size=12)

    for cgm, nome, data, desc in resultados:
        pdf.multi_cell(0, 10, f"CGM: {cgm}\nNome: {nome}\nData: {data}\nDescrição: {desc}\n-------------------------")

    arquivo_pdf = "relatorio_ocorrencias.pdf"
    pdf.output(arquivo_pdf)
    return arquivo_pdf

# Tela de Relatório
def pagina_relatorio():
    st.title("Relatório de Ocorrências 📄")

    data_inicio = st.date_input("Data Início")
    data_fim = st.date_input("Data Fim")

    if st.button("Gerar Relatório"):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cgm, nome, data, descricao FROM ocorrencias
            WHERE date(data) BETWEEN ? AND ?
        """, (str(data_inicio), str(data_fim)))
        resultados = cursor.fetchall()
        conn.close()

        if resultados:
            st.success(f"{len(resultados)} ocorrências encontradas.")
            for cgm, nome, data, desc in resultados:
                st.write(f"CGM: {cgm} - Nome: {nome} - Data: {data} - Descrição: {desc}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Exportar para Word (.docx)"):
                    arquivo_word = exportar_para_word(resultados)
                    with open(arquivo_word, "rb") as file:
                        st.download_button(
                            label="📥 Baixar Relatório Word",
                            data=file,
                            file_name=arquivo_word,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

            with col2:
                if st.button("Exportar para PDF (.pdf)"):
                    arquivo_pdf = exportar_para_pdf(resultados)
                    with open(arquivo_pdf, "rb") as file:
                        st.download_button(
                            label="📥 Baixar Relatório PDF",
                            data=file,
                            file_name=arquivo_pdf,
                            mime="application/pdf"
                        )

        else:
            st.warning("Nenhuma ocorrência encontrada no período selecionado.")

# Menu principal
def menu_principal():
    st.sidebar.title("Menu Principal")
    opcao = st.sidebar.radio("Escolha:", ["Registrar Ocorrência", "Relatórios"])

    if opcao == "Registrar Ocorrência":
        registrar_ocorrencia()
    elif opcao == "Relatórios":
        pagina_relatorio()

# Executa
criar_tabelas()
menu_principal()
