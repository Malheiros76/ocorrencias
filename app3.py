import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
from docx import Document
from docx.shared import Inches
from fpdf import FPDF
import pandas as pd
import urllib.parse
import uuid
import pytz
import hashlib

st.set_page_config(page_title="Sistema Escolar - CCMLC by Malheiros V2.0.3 ", layout="centered")

# --- Estilização Visual ---
st.markdown("""
    <style>
        .stApp {
            background-color: #f2f6fc;
            color: #333333;
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3 {
            color: #003366;
        }
        .block-container {
            max-width: 1000px;
            margin: auto;
            padding: 2rem;
            background-color: white;
            border-radius: 15px;
            box-shadow: 2px 2px 15px rgba(0,0,0,0.1);
        }
        .css-1d391kg {
            padding: 2rem 1rem 2rem 1rem;
        }
        .stButton>button {
            background-color: #003366;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #0055a5;
            transition: 0.3s;
        }
        .stSelectbox, .stTextInput, .stTextArea {
            background-color: #e9f0fa;
            border-radius: 8px;
        }
        .stMarkdown {
            font-size: 1.1rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Conexão com MongoDB ---
@st.cache_resource
def conectar():
    uri = "mongodb+srv://bibliotecaluizcarlos:KAUOQ9ViyKrXDDAl@cluster0.npyoxsi.mongodb.net/?retryWrites=true&w=majority"
    cliente = MongoClient(uri)
    return cliente["escola"]

db = conectar()

print("--- Coleções no banco 'escola' ---")
print(db.list_collection_names())

# --- Funções auxiliares ---
def formatar_mensagem_whatsapp(ocorrencias, nome):
    msg = f"""📋 RELATÓRIO DE OCORRÊNCIAS
👤 Aluno: {nome}
📅 Data do Relatório: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
==============================\n"""

    for i, ocorr in enumerate(ocorrencias, start=1):
        data_txt = ocorr.get("data", "")
        data_formatada = data_txt
        if data_txt:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    data_obj = datetime.strptime(data_txt, fmt)
                    data_formatada = data_obj.strftime("%d/%m/%Y às %H:%M")
                    break
                except ValueError:
                    continue
        msg += f"""
🔸 Ocorrência {i}
📅 Data: {data_formatada}
📝 Descrição: {ocorr['descricao']}
-------------------------"""

    msg += """

👨‍🏫 Escola [CCM Profº Luiz Carlos de Paula e Souza]
📞 Contato: [41 3348-4165]

Este relatório foi gerado automaticamente pelo Sistema de Ocorrências."""
    return msg

# --- Funções para exportar ---
def exportar_ocorrencias_para_word(lista, filename="relatorio.docx"):
    from docx import Document
    from docx.shared import Inches

    doc = Document()

    # Cabeçalho com imagem
    try:
        doc.add_picture("CABECARIOAPP.png", width=Inches(6.0))
    except:
        doc.add_heading("Relatório de Ocorrências", 0)

    for ocorr in lista:
        doc.add_paragraph(f"\nNome do Aluno: {ocorr.get('nome', '')}")
        doc.add_paragraph(f"CGM: {ocorr.get('cgm', '')}")
        doc.add_paragraph(f"Turma: {ocorr.get('turma', '')}")
        doc.add_paragraph(f"Telefone: {ocorr.get('telefone', '')}")
        doc.add_paragraph(f"Data da Ocorrência: {ocorr.get('data', '')}")
        doc.add_paragraph(f"Descrição: {ocorr.get('descricao', '')}")
        doc.add_paragraph("-" * 50)

    doc.add_paragraph("\n\n" + "_" * 30 + "                      " + "_" * 30)
    doc.add_paragraph("Assinatura do Funcionário                Assinatura do Responsável")

    doc.save(filename)
    return filename


def exportar_ocorrencias_para_pdf(lista, filename="relatorio.pdf"):
    from fpdf import FPDF
    import os

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Cabeçalho com imagem
    if os.path.exists("CABECARIOAPP.png"):
        pdf.image("CABECARIOAPP.png", x=10, y=8, w=190)
        pdf.ln(35)
    else:
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Relatório de Ocorrências", ln=True, align='C')

    pdf.set_font("Arial", size=12)

    for ocorr in lista:
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Aluno: {ocorr.get('nome', '')}", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 10, f"CGM: {ocorr.get('cgm', '')}", ln=True)
        pdf.cell(0, 10, f"Turma: {ocorr.get('turma', '')}", ln=True)
        pdf.cell(0, 10, f"Telefone: {ocorr.get('telefone', '')}", ln=True)
        pdf.cell(0, 10, f"Data: {ocorr.get('data', '')}", ln=True)
        pdf.multi_cell(0, 10, f"Descrição: {ocorr.get('descricao', '')}")
        pdf.cell(0, 10, "-" * 70, ln=True)

    pdf.ln(20)
    pdf.cell(90, 10, "_________________________", 0, 0, "C")
    pdf.cell(10)
    pdf.cell(90, 10, "_________________________", 0, 1, "C")
    pdf.cell(90, 10, "Funcionário", 0, 0, "C")
    pdf.cell(10)
    pdf.cell(90, 10, "Responsável", 0, 1, "C")

    pdf.output(filename)
    return filename

# --- Login ---
def pagina_login():
    st.markdown("## 👤 Login de Usuário - V2.0.3 LSM")
    usuario = st.text_input("Usuário").strip()
    senha = st.text_input("Senha", type="password").strip()

    if st.button("Entrar"):
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        user = db.usuarios.find_one({
            "usuario": usuario,
            "senha": senha_hash
        })

        if user:
            st.session_state["logado"] = True
            st.session_state["usuario"] = usuario
            st.session_state["nivel"] = user.get("nivel", "user")
            st.success("✅ Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# --- Cadastro de Alunos ---
def pagina_cadastro():
    st.markdown("## ✏️ Cadastro de Alunos")

    # --- Lista de alunos cadastrados ---
    alunos = list(db.alunos.find().sort("nome", 1))

    nomes_exibicao = [""] + [
        f"{a['nome']} (CGM: {a['cgm']})"
        for a in alunos
    ]

    selecionado = st.selectbox("🔎 Buscar aluno para Alterar ou Excluir:", nomes_exibicao)

    aluno_carregado = None
    if selecionado and selecionado != "":
        # Extrai CGM do texto selecionado
        cgm_busca = selecionado.split("CGM:")[1].replace(")", "").strip()
        aluno_carregado = db.alunos.find_one({"cgm": cgm_busca})

        st.success(f"Aluno carregado: {aluno_carregado['nome']} (CGM {aluno_carregado['cgm']})")

    # --- Formulário de Cadastro ou Alteração ---
    with st.form("form_cadastro"):

        cgm = st.text_input("CGM", value=aluno_carregado["cgm"] if aluno_carregado else "")
        nome = st.text_input("Nome", value=aluno_carregado["nome"] if aluno_carregado else "")
        data = st.date_input("Data de Nascimento",
                             value=pd.to_datetime(aluno_carregado["data"]).date()
                             if aluno_carregado and aluno_carregado.get("data") else datetime.now().date())
        telefone = st.text_input("Telefone", value=aluno_carregado["telefone"] if aluno_carregado else "")
        responsavel = st.text_input("Responsável", value=aluno_carregado["responsavel"] if aluno_carregado else "")
        turma = st.text_input("Turma", value=aluno_carregado["turma"] if aluno_carregado else "")

        col1, col2, col3 = st.columns([1,1,1])
        salvar = col1.form_submit_button("💾 Salvar / Alterar")
        excluir = col2.form_submit_button("🗑️ Excluir")
        limpar = col3.form_submit_button("🧹 Limpar")

    # --- Ações após clique ---
    if salvar:
        if cgm and nome:
            db.alunos.update_one({"cgm": cgm}, {
                "$set": {
                    "cgm": cgm,
                    "nome": nome,
                    "data": str(data),
                    "telefone": telefone,
                    "responsavel": responsavel,
                    "turma": turma
                }
            }, upsert=True)
            st.success("✅ Aluno salvo ou atualizado com sucesso!")
            st.experimental_rerun()
        else:
            st.error("Preencha todos os campos obrigatórios.")

    if excluir and aluno_carregado:
        confirmacao = st.warning(f"Tem certeza que deseja excluir o aluno {aluno_carregado['nome']} (CGM {aluno_carregado['cgm']})?")
        if st.button("✅ Confirmar Exclusão"):
            db.alunos.delete_one({"cgm": aluno_carregado["cgm"]})
            st.success("✅ Aluno excluído com sucesso!")
            st.experimental_rerun()

    if limpar:
        st.experimental_rerun()

    # --- Importação de alunos via arquivo ---
    st.subheader("📥 Importar Alunos via TXT ou CSV")
    arquivo = st.file_uploader("Escolha o arquivo .txt ou .csv", type=["txt", "csv"])
    delimitador = st.selectbox("Escolha o delimitador", [";", ",", "\\t"])
    delimitador_real = {";": ";", ",": ",", "\\t": "\t"}[delimitador]

    if arquivo is not None:
        try:
            df_import = pd.read_csv(arquivo, delimiter=delimitador_real)
            df_import.columns = [col.strip().lower() for col in df_import.columns]
            st.dataframe(df_import)

            if st.button("Importar para o Sistema"):
                erros = []
                total_importados = 0
                for _, row in df_import.iterrows():
                    try:
                        cgm = str(row.get('cgm', '')).strip()
                        nome = str(row.get('nome', '')).strip()
                        data_nasc = row.get('data', datetime.now().strftime("%Y-%m-%d"))
                        telefone = str(row.get('telefone', '')).strip()
                        responsavel = str(row.get('responsavel', '')).strip()
                        turma = str(row.get('turma', '')).strip()

                        if not cgm or not nome:
                            erros.append(f"Linha {_+2}: CGM ou Nome vazio.")
                            continue

                        db.alunos.update_one({"cgm": cgm}, {
                            "$set": {
                                "cgm": cgm,
                                "nome": nome,
                                "data": str(data_nasc),
                                "telefone": telefone,
                                "responsavel": responsavel,
                                "turma": turma
                            }
                        }, upsert=True)
                        total_importados += 1
                    except Exception as e:
                        erros.append(f"Linha {_+2}: {str(e)}")

                st.success(f"Importação finalizada: {total_importados} registros importados.")
                if erros:
                    st.error("Ocorreram erros:")
                    for e in erros:
                        st.write(e)

        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# --- Registro de Ocorrências ---
def pagina_ocorrencias():
    st.markdown("## 🚨 Registro de Ocorrência")

    alunos = list(db.alunos.find())
    alunos_ordenados = sorted(alunos, key=lambda x: x['nome'])

    busca_cgm = st.text_input("🔍 Buscar aluno por CGM")

    aluno_selecionado = None
    if busca_cgm:
        for a in alunos_ordenados:
            if a['cgm'] == busca_cgm:
                aluno_selecionado = a
                break

    if aluno_selecionado:
        st.success(f"Aluno: {aluno_selecionado['nome']} (CGM {aluno_selecionado['cgm']})")

        descricao = st.text_area("Descreva a ocorrência")
        data_ocorrencia = st.date_input("Data da Ocorrência", value=datetime.now())
        hora_ocorrencia = st.time_input("Hora da Ocorrência", value=datetime.now().time())

        if st.button("Salvar Ocorrência"):
            if descricao.strip() == "":
                st.error("Descrição da ocorrência não pode ficar vazia.")
            else:
                dt_string = datetime.combine(data_ocorrencia, hora_ocorrencia).strftime("%Y-%m-%d %H:%M:%S")
                nova_ocorrencia = {
                    "aluno_id": aluno_selecionado.get("_id"),
                    "nome": aluno_selecionado.get("nome"),
                    "cgm": aluno_selecionado.get("cgm"),
                    "data": dt_string,
                    "descricao": descricao,
                    "turma": aluno_selecionado.get("turma", ""),
                    "telefone": aluno_selecionado.get("telefone", ""),
                    "responsavel": aluno_selecionado.get("responsavel", "")
                }
                db.ocorrencias.insert_one(nova_ocorrencia)
                st.success("Ocorrência salva com sucesso!")

                # Exibir mensagem para WhatsApp
                msg = formatar_mensagem_whatsapp([nova_ocorrencia], aluno_selecionado.get("nome"))
                st.text_area("Mensagem para WhatsApp:", value=msg, height=200)

    else:
        st.info("Digite um CGM válido para buscar o aluno.")

# --- Consulta Ocorrências por CGM - NOVA ABA ---
def pagina_consulta_ocorrencias():
    st.markdown("## 🔍 Consulta de Ocorrências por CGM")

    cgm_consulta = st.text_input("Digite o CGM do aluno")

    if cgm_consulta:
        ocorrencias = list(db.ocorrencias.find({"cgm": cgm_consulta}).sort("data", -1))

        if not ocorrencias:
            st.warning("Nenhuma ocorrência encontrada para este CGM.")
        else:
            nome_aluno = ocorrencias[0].get("nome", "Nome não encontrado")
            st.success(f"Exibindo ocorrências para: {nome_aluno} (CGM {cgm_consulta})")

            for i, ocorr in enumerate(ocorrencias, start=1):
                st.markdown(f"### Ocorrência {i}")
                st.write(f"**Data:** {ocorr.get('data', '')}")
                st.write(f"**Descrição:** {ocorr.get('descricao', '')}")
                st.write("---")

            # Exportação de ocorrências
            st.markdown("### Exportar ocorrências")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Exportar para Word"):
                    filename = f"relatorio_{cgm_consulta}.docx"
                    exportar_ocorrencias_para_word(ocorrencias, filename)
                    with open(filename, "rb") as file:
                        st.download_button("Clique para baixar o arquivo Word", data=file, file_name=filename, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

            with col2:
                if st.button("Exportar para PDF"):
                    filename = f"relatorio_{cgm_consulta}.pdf"
                    exportar_ocorrencias_para_pdf(ocorrencias, filename)
                    with open(filename, "rb") as file:
                        st.download_button("Clique para baixar o arquivo PDF", data=file, file_name=filename, mime="application/pdf")

            with col3:
                msg_whatsapp = formatar_mensagem_whatsapp(ocorrencias, nome_aluno)
                st.text_area("Mensagem para WhatsApp", value=msg_whatsapp, height=200)

# --- Cadastro de Usuários ---
def pagina_cadastro_usuarios():
    st.markdown("## 👨‍💻 Cadastro e Gerenciamento de Usuários")

    usuarios = list(db.usuarios.find())
    usuarios_ordenados = sorted(usuarios, key=lambda x: x['usuario'])

    usuario_selecionado = st.selectbox("Selecionar usuário para alterar/excluir", [""] + [u["usuario"] for u in usuarios_ordenados])

    usuario_atual = None
    if usuario_selecionado:
        usuario_atual = db.usuarios.find_one({"usuario": usuario_selecionado})

    with st.form("form_usuario"):
        usuario = st.text_input("Usuário", value=usuario_atual["usuario"] if usuario_atual else "")
        senha = st.text_input("Senha (deixe em branco para não alterar)", type="password")
        nivel = st.selectbox("Nível de Acesso", options=["admin", "user"], index=0 if not usuario_atual else (0 if usuario_atual.get("nivel", "user") == "admin" else 1))

        salvar = st.form_submit_button("Salvar / Alterar")
        excluir = st.form_submit_button("Excluir")
        limpar = st.form_submit_button("Limpar")

    if salvar:
        if usuario:
            senha_hash = usuario_atual.get("senha") if (usuario_atual and senha.strip() == "") else hashlib.sha256(senha.encode()).hexdigest()
            db.usuarios.update_one({"usuario": usuario}, {"$set": {"usuario": usuario, "senha": senha_hash, "nivel": nivel}}, upsert=True)
            st.success("Usuário salvo ou alterado com sucesso!")
            st.experimental_rerun()
        else:
            st.error("Usuário não pode ficar vazio.")

    if excluir and usuario_atual:
        db.usuarios.delete_one({"usuario": usuario_atual["usuario"]})
        st.success("Usuário excluído com sucesso!")
        st.experimental_rerun()

    if limpar:
        st.experimental_rerun()

# --- Função para logout ---
def logout():
    st.session_state["logado"] = False
    st.session_state["usuario"] = ""
    st.session_state["nivel"] = ""

# --- Menu principal ---
def menu():
    st.sidebar.title(f"Bem-vindo, {st.session_state['usuario']}")

    menu = st.sidebar.radio("Menu", [
        "Registro de Ocorrências",
        "Consulta Ocorrências",
        "Cadastro de Alunos",
        "Cadastro de Usuários",
        "Sair"
    ])

    if menu == "Registro de Ocorrências":
        pagina_ocorrencias()
    elif menu == "Consulta Ocorrências":
        pagina_consulta_ocorrencias()
    elif menu == "Cadastro de Alunos":
        pagina_cadastro()
    elif menu == "Cadastro de Usuários":
        if st.session_state["nivel"] == "admin":
            pagina_cadastro_usuarios()
        else:
            st.warning("Você não tem permissão para acessar esta área.")
    elif menu == "Sair":
        logout()
        st.experimental_rerun()

# --- Execução ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["usuario"] = ""
    st.session_state["nivel"] = ""

if not st.session_state["logado"]:
    pagina_login()
else:
    menu()
