import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
from docx import Document
from docx.shared import Inches
from fpdf import FPDF
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Sistema Escolar - CCMLC by Malheiros ", layout="centered")

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
        try:
            data_obj = datetime.strptime(ocorr["data"], "%Y-%m-%d %H:%M:%S")
        except:
            data_obj = datetime.strptime(ocorr["data"], "%Y-%m-%d %H:%M")
        data_formatada = data_obj.strftime('%d/%m/%Y às %H:%M')
        msg += f"""
🔸 Ocorrência {i}
📅 Data: {data_formatada}
📝 Descrição: {ocorr['descricao']}\n-------------------------"""
    msg += """

👨‍🏫 Escola [CCM Profº Luiz Carlos de Paula e Souza ]
📞 Contato: [41 3348-4165]

Este relatório foi gerado automaticamente pelo Sistema de Ocorrências."""
    return msg
def exportar_ocorrencias_para_word(resultados):
    doc = Document()
    doc.add_picture("CABECARIOAPP.png", width=Inches(6))
    doc.add_heading("Relatório de Ocorrências", level=1)
    for ocorr in resultados:
        doc.add_paragraph(f"CGM: {ocorr['cgm']}\nNome: {ocorr['nome']}\nData: {ocorr['data']}\nDescrição: {ocorr['descricao']}\nServidor: {ocorr.get('servidor', '')}\n----------------------")
    doc.add_paragraph("\n\nAssinatura do Servidor: ____________________________")
    doc.add_paragraph("\nAssinatura do Responsável: ____________________________")
    doc.add_paragraph("\nData: _______/_______/_________")
    caminho = "relatorio_ocorrencias.docx"
    doc.save(caminho)
    return caminho

def exportar_ocorrencias_para_pdf(resultados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    try:
        pdf.image("CABECARIOAPP.png", x=10, y=8, w=190)
    except:
        pass
    pdf.ln(35)
    pdf.cell(0, 10, "Relatório de Ocorrências", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    for ocorr in resultados:
        pdf.multi_cell(0, 8, f"CGM: {ocorr['cgm']}\nNome: {ocorr['nome']}\nData: {ocorr['data']}\nDescrição: {ocorr['descricao']}\nServidor: {ocorr.get('servidor', '')}")
        pdf.cell(0, 0, "-" * 70, ln=True)
        pdf.ln(5)
    pdf.ln(10)
    pdf.cell(0, 10, "Assinatura do Servidor: ____________________________", ln=True)
    pdf.cell(0, 10, "Assinatura do Responsável: _________________________", ln=True)
    pdf.cell(0, 10, "Data: ______/______/________", ln=True)
    caminho = "relatorio_ocorrencias.pdf"
    pdf.output(caminho)
    return caminho

# --- Login ---
def pagina_login():
    st.markdown("## 👤 Login de Usuário - V2.0 LSM")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = db.usuarios.find_one({"usuario": usuario, "senha": senha})
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
    with st.form("form_cadastro"):
        cgm = st.text_input("CGM")
        nome = st.text_input("Nome")
        data = st.date_input("Data de Nascimento")
        telefone = st.text_input("Telefone")
        responsavel = st.text_input("Responsável")
        turma = st.text_input("Turma")
        enviado = st.form_submit_button("Salvar")

    if enviado:
        if cgm and nome:
            db.alunos.update_one({"cgm": cgm}, {"$set": {
                "cgm": cgm,
                "nome": nome,
                "data": str(data),
                "telefone": telefone,
                "responsavel": responsavel,
                "turma": turma
            }}, upsert=True)
            st.success("✅ Aluno cadastrado com sucesso!")
        else:
            st.error("Preencha todos os campos obrigatórios.")

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
                        data = str(row.get('data', '')).strip()
                        telefone = str(row.get('telefone', '')).strip()
                        responsavel = str(row.get('responsavel', '')).strip()
                        turma = str(row.get('turma', '')).strip()

                        if not cgm or not nome:
                            erros.append(f"CGM ou Nome ausente na linha: {row.to_dict()}")
                            continue

                        aluno = {
                            "cgm": cgm,
                            "nome": nome,
                            "data": data,
                            "telefone": telefone,
                            "responsavel": responsavel,
                            "turma": turma
                        }

                        db.alunos.update_one({"cgm": cgm}, {"$set": aluno}, upsert=True)
                        total_importados += 1

                    except Exception as e:
                        erros.append(f"Erro na linha {row.to_dict()} → {e}")

                st.success(f"✅ Importação finalizada. Total importado/atualizado: {total_importados}")
                if erros:
                    st.warning("⚠️ Erros encontrados:")
                    for erro in erros:
                        st.error(erro)

        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

# --- Registro de Ocorrência ---
def pagina_ocorrencias():
    st.markdown("## 🚨 Registro de Ocorrência")

    alunos = list(db.alunos.find())
    alunos_ordenados = sorted(alunos, key=lambda x: x['nome'])

    busca_cgm = st.text_input("🔍 Buscar aluno por CGM")

    # Se o CGM for digitado, tenta encontrar aluno
    if busca_cgm:
        aluno_cgm = next((a for a in alunos_ordenados if a["cgm"] == busca_cgm), None)
        if aluno_cgm:
            nomes = [f"{aluno_cgm['nome']} (CGM: {aluno_cgm['cgm']})"]
        else:
            st.warning("Nenhum aluno encontrado com esse CGM.")
            return
    else:
        nomes = [""] + [f"{a['nome']} (CGM: {a['cgm']})" for a in alunos_ordenados]  # Adiciona item em branco

    if nomes:
        selecionado = st.selectbox("Selecione o aluno:", nomes)

        if selecionado != "":
            cgm = selecionado.split("CGM: ")[1].replace(")", "")
            nome = selecionado.split(" (CGM:")[0]

            descricao = st.text_area("Descrição da Ocorrência")
            registrar = st.button("Registrar Ocorrência")

            if registrar and descricao:
                agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                telefone = next((a['telefone'] for a in alunos if a['cgm'] == cgm), "")
                db.ocorrencias.insert_one({
                    "cgm": cgm,
                    "nome": nome,
                    "telefone": telefone,
                    "data": agora,
                    "descricao": descricao
                })
                st.success("✅ Ocorrência registrada com sucesso!")

# --- Exportar Relatórios ---
def pagina_exportar():
    from docx import Document
    from docx.shared import Inches
    from fpdf import FPDF

    st.markdown("## 📥 Exportar Relatórios")
    resultados = list(db.ocorrencias.find({}, {"_id": 0}))

    if not resultados:
        st.warning("Nenhuma ocorrência encontrada.")
        return
    # Exportar por CGM
    st.subheader("🔍 Buscar por CGM")
    cgm_input = st.text_input("Digite o CGM do aluno para gerar o relatório")
    col1, col2 = st.columns(2)
    if col1.button("📄 Gerar Word por CGM") and cgm_input:
        resultados_filtrados = list(db.ocorrencias.find({"cgm": cgm_input}))
        if resultados_filtrados:
            caminho = exportar_ocorrencias_para_word(resultados_filtrados)
            with open(caminho, "rb") as f:
                st.download_button("📥 Baixar Word", f, file_name="ocorrencias_cgm.docx")
        else:
            st.warning("Nenhuma ocorrência encontrada para este CGM.")
    if col2.button("🧾 Gerar PDF por CGM") and cgm_input:
        resultados_filtrados = list(db.ocorrencias.find({"cgm": cgm_input}))
        if resultados_filtrados:
            caminho = exportar_ocorrencias_para_pdf(resultados_filtrados)
            with open(caminho, "rb") as f:
                st.download_button("📥 Baixar PDF", f, file_name="ocorrencias_cgm.pdf")
        else:
            st.warning("Nenhuma ocorrência encontrada para este CGM.")


 # --- Botões para exportar tudo ---
    st.subheader("📦 Exportar Todas as Ocorrências")
    if resultados:
        nome_primeiro = resultados[0].get("nome", "relatorio").replace(" ", "_").upper()
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Gerar Word"):
                caminho = exportar_ocorrencias_para_word(resultados)
                with open(caminho, "rb") as f:
                    st.download_button("📥 Baixar Word", f, file_name=f"{nome_primeiro}.docx")

        with col2:
            if st.button("🧾 Gerar PDF"):
                caminho = exportar_ocorrencias_para_pdf(resultados)
                with open(caminho, "rb") as f:
                    st.download_button("📥 Baixar PDF", f, file_name=f"{nome_primeiro}.pdf")
        with col3:
               st.info("Mensagens individuais abaixo ⬇️")


    # Agrupar por aluno e exibir relatórios com WhatsApp
    ocorrencias_por_aluno = {}
    for ocorr in resultados:
        nome = ocorr.get("nome", "")
        if nome not in ocorrencias_por_aluno:
            ocorrencias_por_aluno[nome] = []
        ocorrencias_por_aluno[nome].append(ocorr)

    for nome, lista in sorted(ocorrencias_por_aluno.items()):
        with st.expander(f"📄 Relatório de {nome}"):
            telefone = lista[0].get("telefone", "")
            for ocorr in lista:
                st.write(f"📅 {ocorr['data']} - 📝 {ocorr['descricao']}")

            mensagem = formatar_mensagem_whatsapp(lista, nome)
            st.text_area("📋 WhatsApp", mensagem, height=200)

            if telefone:
                numero = telefone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
                link = f"https://api.whatsapp.com/send?phone=55{numero}&text={urllib.parse.quote(mensagem)}"
                st.markdown(f"[📱 Enviar para {telefone}]({link})")

# --- Lista de Alunos ---
def pagina_lista():
    st.markdown("## 📄 Lista de Alunos")
    dados = list(db.alunos.find({}, {"_id": 0}))
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df.sort_values("nome"))
    else:
        st.info("Nenhum aluno cadastrado.")

# --- Cadastro de Usuários ---
def pagina_usuarios():
    st.markdown("## 👥 Cadastro de Usuários")
    if cadastrar:
    usuario = usuario.strip()
    senha = senha.strip()
    if usuario and senha:
        try:
            resultado = db.usuarios.insert_one({
                "usuario": usuario,
                "senha": senha,
                "nivel": nivel
            })
            st.success("✅ Usuário cadastrado com sucesso!")
            print("Usuário salvo com id:", resultado.inserted_id)
        except Exception as e:
            print("Erro ao salvar usuário:", e)
            st.error(f"Erro ao salvar usuário: {e}")
    else:
        st.error("Preencha todos os campos.")

# --- Menu Lateral ---
def menu():
    st.sidebar.image("BRASÃO.png", use_container_width=True)
    st.sidebar.markdown("### 📚 Menu de Navegação")
    opcoes = ["Cadastro", "Ocorrências", "Exportar", "Lista"]
    if st.session_state.get("nivel") == "admin":
        opcoes.append("Usuários")
    pagina = st.sidebar.selectbox("Escolha a aba:", opcoes)

    if pagina == "Cadastro":
        pagina_cadastro()
    elif pagina == "Ocorrências":
        pagina_ocorrencias()
    elif pagina == "Exportar":
        pagina_exportar()
    elif pagina == "Lista":
        pagina_lista()
    elif pagina == "Usuários":
        pagina_usuarios()

def sair():
    st.session_state["logado"] = False
    st.session_state["usuario"] = ""
    st.session_state["nivel"] = ""
    st.rerun()
    
# --- Execução ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    pagina_login()
else:
    if st.sidebar.button("🚪 Sair do Sistema"):
        sair()
    else:
        menu()

