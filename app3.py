import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import pytz
import io
import urllib.parse

# ================= CONFIG =================
st.set_page_config(
    page_title="Sistema Escolar - CCMLC ULTRA V2.3",
    layout="centered"
)

# ================= CONEXÃO ÚNICA =================
@st.cache_resource
def conectar():
    uri = "SUA_URI_AQUI"
    cliente = MongoClient(uri)
    db = cliente["escola"]

    try:
        db.ocorrencias.create_index([("cgm", 1), ("data", -1)])
        db.ocorrencias.create_index([("nome", 1), ("data", -1)])
        db.ocorrencias.create_index("data")
        db.alunos.create_index("cgm")
        db.alunos.create_index("nome")
    except:
        pass

    return db

db = conectar()

# ================= UTIL =================
def agora_local():
    tz = pytz.timezone("America/Sao_Paulo")
    return datetime.now(tz)

# ================= BUSCAS =================
@st.cache_data(ttl=120)
def buscar_por_cgm(cgm):
    return list(
        db.ocorrencias.find(
            {"cgm": cgm},
            {"_id": 0, "nome": 1, "telefone": 1, "data": 1, "descricao": 1}
        ).sort("data", -1)
    )

@st.cache_data(ttl=120)
def listar_alunos():
    return list(
        db.alunos.find({}, {"_id": 0, "nome": 1}).sort("nome", 1)
    )

@st.cache_data(ttl=60)
def contar_ocorrencias(nome):
    return db.ocorrencias.count_documents({"nome": nome})

@st.cache_data(ttl=60)
def buscar_ocorrencias_paginadas(nome, skip, limit):
    return list(
        db.ocorrencias.find(
            {"nome": nome},
            {"_id": 0, "data": 1, "descricao": 1, "telefone": 1}
        )
        .sort("data", -1)
        .skip(skip)
        .limit(limit)
    )

# ================= EXPORT =================
def exportar_word(lista):
    buffer = io.BytesIO()
    doc = Document()
    doc.add_heading("RELATÓRIO DE OCORRÊNCIAS", level=1)

    for o in lista:
        doc.add_paragraph(f"Data: {o.get('data','')}")
        doc.add_paragraph(f"Descrição: {o.get('descricao','')}")
        doc.add_paragraph("-" * 40)

    doc.save(buffer)
    buffer.seek(0)
    return buffer

def exportar_pdf(lista):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("RELATÓRIO DE OCORRÊNCIAS", styles["Heading1"]))
    elements.append(Spacer(1, 12))

    for o in lista:
        texto = f"Data: {o.get('data','')}<br/>Descrição: {o.get('descricao','')}"
        elements.append(Paragraph(texto, styles["Normal"]))
        elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ================= WHATSAPP =================
@st.cache_data(ttl=300)
def gerar_msg_cache(lista_serializada, nome):
    msg = f"📋 RELATÓRIO DE OCORRÊNCIAS\nAluno: {nome}\n\n"
    for i, o in enumerate(lista_serializada, 1):
        msg += f"{i}) {o[0]} - {o[1]}\n"
    return msg

# ================= PÁGINA EXPORTAR =================
def pagina_exportar():
    st.markdown("## 📥 Exportar Relatórios")

    # ===== BUSCAR POR CGM =====
    st.subheader("🔍 Buscar por CGM")
    cgm_input = st.text_input("Digite o CGM do aluno")

    if st.button("Buscar", key="buscar_cgm") and cgm_input:
        dados = buscar_por_cgm(cgm_input)

        if dados:
            st.success(f"{len(dados)} ocorrência(s) encontrada(s)")

            col1, col2 = st.columns(2)

            if col1.button("📄 Gerar DOCX"):
                with st.spinner("Gerando..."):
                    arquivo = exportar_word(dados)
                st.download_button("Baixar DOCX", arquivo,
                    file_name=f"ocorrencias_{cgm_input}.docx")

            if col2.button("🧾 Gerar PDF"):
                with st.spinner("Gerando..."):
                    arquivo = exportar_pdf(dados)
                st.download_button("Baixar PDF", arquivo,
                    file_name=f"ocorrencias_{cgm_input}.pdf")
        else:
            st.warning("Nenhuma ocorrência encontrada.")

    # ===== RELATÓRIO INDIVIDUAL SOB DEMANDA =====
    st.subheader("📄 Relatórios Individuais por Aluno")

    alunos = listar_alunos()

    for aluno in alunos:
        nome = aluno["nome"]

        with st.expander(f"📄 {nome}"):

            total = contar_ocorrencias(nome)

            if total == 0:
                st.info("Nenhuma ocorrência.")
                continue

            page_size = 30
            paginas = max(1, (total // page_size) + (1 if total % page_size else 0))

            pagina = st.number_input(
                "Página",
                min_value=1,
                max_value=paginas,
                value=1,
                key=f"page_{nome}"
            )

            skip = (pagina - 1) * page_size
            dados = buscar_ocorrencias_paginadas(nome, skip, page_size)

            for o in dados:
                st.write(f"{o['data']} - {o['descricao']}")

            telefone = dados[0]["telefone"] if dados else ""

            lista_serializada = tuple((o["data"], o["descricao"]) for o in dados)
            mensagem = gerar_msg_cache(lista_serializada, nome)

            st.text_area("WhatsApp", mensagem, height=200)

            if telefone:
                numero = ''.join(filter(str.isdigit, telefone))
                link = f"https://api.whatsapp.com/send?phone=55{numero}&text={urllib.parse.quote(mensagem)}"
                st.markdown(f"[📱 Enviar para {telefone}]({link})")

            col1, col2 = st.columns(2)

            if col1.button("📄 DOCX", key=f"doc_{nome}"):
                with st.spinner("Gerando..."):
                    todas = buscar_ocorrencias_paginadas(nome, 0, total)
                    arquivo = exportar_word(todas)
                st.download_button("Baixar DOCX", arquivo,
                    file_name=f"{nome}.docx",
                    key=f"down_doc_{nome}")

            if col2.button("🧾 PDF", key=f"pdf_{nome}"):
                with st.spinner("Gerando..."):
                    todas = buscar_ocorrencias_paginadas(nome, 0, total)
                    arquivo = exportar_pdf(todas)
                st.download_button("Baixar PDF", arquivo,
                    file_name=f"{nome}.pdf",
                    key=f"down_pdf_{nome}")

# ================= LOGIN SIMPLES =================
if "logado" not in st.session_state:
    st.session_state["logado"] = True  # modo teste

if st.session_state["logado"]:
    pagina_exportar()
