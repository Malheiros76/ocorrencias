import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import urllib.parse
import os

# ===== Banco de Dados =====
def conectar():
    return sqlite3.connect("ocorrencias.db", check_same_thread=False)

def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()
    # Alunos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            cgm TEXT PRIMARY KEY,
            nome TEXT,
            telefone TEXT
        )
    """)
    # Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            usuario TEXT UNIQUE,
            senha TEXT,
            setor TEXT
        )
    """)
    # Ocorrências
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT,
            nome TEXT,
            telefone TEXT,
            data TEXT,
            descricao TEXT
        )
    """)
    conn.commit()
    conn.close()

# ===== Função para desenhar cabeçalho com imagem no PDF =====
def desenhar_cabecalho_pdf(c):
    caminho_imagem = os.path.join(os.getcwd(), "CABEÇARIOAPP.png")
    try:
        if os.path.exists(caminho_imagem):
            logo = ImageReader(caminho_imagem)
            largura_imagem = 350  # largura da imagem no PDF (ajuste se quiser)
            altura_imagem = 80    # altura da imagem no PDF (aprox)
            x = (A4[0] - largura_imagem) / 2  # centraliza horizontalmente
            y = A4[1] - altura_imagem - 20    # 20 pts da borda superior
            c.drawImage(logo, x, y, width=largura_imagem, height=altura_imagem, preserveAspectRatio=True)
        else:
            print(f"Imagem não encontrada: {caminho_imagem}")
    except Exception as e:
        print(f"Erro ao desenhar imagem no PDF: {e}")

# ===== Formatar mensagem WhatsApp =====
def formatar_mensagem_whatsapp(ocorrencias_aluno, nome_aluno):
    mensagem = f"📋 *RELATÓRIO DE OCORRÊNCIAS*\n"
    mensagem += f"👤 *Aluno:* {nome_aluno}\n"
    mensagem += f"📅 *Data do Relatório:* {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n"
    mensagem += "="*30 + "\n\n"
    for i, (cgm, nome, data, desc, telefone) in enumerate(ocorrencias_aluno, 1):
        try:
            data_formatada = datetime.strptime(data, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y às %H:%M")
        except:
            data_formatada = data
        mensagem += f"🔸 *Ocorrência {i}*\n"
        mensagem += f"📅 Data: {data_formatada}\n"
        mensagem += f"📝 Descrição: {desc}\n"
        mensagem += "-"*25 + "\n\n"
    mensagem += "👨‍🏫 *Escola CCM Profº Luiz Carlos de Paula e Souza*\n"
    mensagem += "📞 Contato: (41) 3348-4165\n\n"
    mensagem += "_Este relatório foi gerado automaticamente pelo Sistema de Ocorrências._"
    return mensagem

# ===== Página: Cadastro de Alunos =====
def pagina_cadastro_alunos():
    st.header("Cadastro de Alunos 👦👧")
    cgm = st.text_input("CGM")
    nome = st.text_input("Nome")
    telefone = st.text_input("Telefone")
    if st.button("Salvar Aluno"):
        if cgm.strip() and nome.strip():
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (cgm.strip(), nome.strip(), telefone.strip()))
            conn.commit()
            conn.close()
            st.success("Aluno salvo com sucesso!")
        else:
            st.warning("Preencha CGM e Nome obrigatoriamente.")

    # Importar via TXT
    st.subheader("Importar Alunos via TXT")
    arquivo_txt = st.file_uploader("Escolha arquivo TXT", type=["txt"])
    if arquivo_txt is not None:
        df = pd.read_csv(arquivo_txt, sep=",", header=None, names=["CGM", "Nome", "Telefone"])
        st.dataframe(df)
        if st.button("Importar Alunos do TXT"):
            conn = conectar()
            cursor = conn.cursor()
            for _, row in df.iterrows():
                cursor.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (str(row["CGM"]).strip(), str(row["Nome"]).strip(), str(row["Telefone"]).strip()))
            conn.commit()
            conn.close()
            st.success("Importação concluída!")

# ===== Página: Cadastro de Usuário =====
def pagina_cadastro_usuario():
    st.header("Cadastro de Usuário 🧑‍💼")
    nome = st.text_input("Nome completo")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    setor = st.text_input("Setor")

    if st.button("Cadastrar Usuário"):
        if nome.strip() and usuario.strip() and senha.strip():
            conn = conectar()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO usuarios (nome, usuario, senha, setor) VALUES (?, ?, ?, ?)", (nome.strip(), usuario.strip(), senha.strip(), setor.strip()))
                conn.commit()
                st.success("Usuário cadastrado!")
            except sqlite3.IntegrityError:
                st.error("Usuário já existe!")
            finally:
                conn.close()
        else:
            st.warning("Preencha todos os campos obrigatórios.")

# ===== Página: Lista de Alunos =====
def pagina_lista_alunos():
    st.header("Lista de Alunos (Ordem Alfabética)")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT cgm, nome, telefone FROM alunos ORDER BY nome ASC")
    alunos = cursor.fetchall()
    conn.close()
    if alunos:
        df = pd.DataFrame(alunos, columns=["CGM", "Nome", "Telefone"])
        st.dataframe(df)
    else:
        st.info("Nenhum aluno cadastrado.")

# ===== Página: Registro de Ocorrências =====
def pagina_ocorrencias():
    st.header("Registro de Ocorrências 📋")
    cgm_busca = st.text_input("CGM do aluno")
    nome, telefone = "", ""
    if cgm_busca:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, telefone FROM alunos WHERE cgm=?", (cgm_busca.strip(),))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            nome, telefone = resultado
            st.info(f"Nome: {nome} | Telefone: {telefone}")
        else:
            st.warning("Aluno não encontrado.")
    descricao = st.text_area("Descrição da Ocorrência")
    if st.button("Salvar Ocorrência"):
        if cgm_busca.strip() and descricao.strip():
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ocorrencias (cgm, nome, telefone, data, descricao) VALUES (?, ?, ?, ?, ?)", (cgm_busca.strip(), nome, telefone, data_atual, descricao.strip()))
            conn.commit()
            conn.close()
            st.success("Ocorrência salva!")
            st.experimental_rerun()
        else:
            st.warning("Preencha CGM e descrição da ocorrência.")

    # Listar ocorrências
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, cgm, nome, data, descricao FROM ocorrencias ORDER BY data DESC")
    ocorrencias = cursor.fetchall()
    conn.close()

    if ocorrencias:
        st.subheader("Ocorrências Registradas")
        for id_, cgm_, nome_, data_, desc_ in ocorrencias:
            with st.expander(f"{id_} - {nome_} ({cgm_}) - {data_}"):
                st.write("**Descrição atual:**")
                st.write(desc_)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✏️ Alterar {id_}", key=f"alt_{id_}"):
                        st.session_state[f"editando_{id_}"] = True
                        st.experimental_rerun()
                with col2:
                    if st.button(f"🗑️ Excluir {id_}", key=f"del_{id_}"):
                        conn = conectar()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM ocorrencias WHERE id=?", (id_,))
                        conn.commit()
                        conn.close()
                        st.success("Ocorrência excluída!")
                        st.experimental_rerun()
                if st.session_state.get(f"editando_{id_}", False):
                    st.markdown("---")
                    st.write("**Editando Ocorrência:**")
                    nova_desc = st.text_area("Nova descrição:", value=desc_, key=f"nova_desc_{id_}", height=100)
                    col_salvar, col_cancelar = st.columns(2)
                    with col_salvar:
                        if st.button("💾 Salvar", key=f"save_{id_}"):
                            if nova_desc.strip():
                                conn = conectar()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE ocorrencias SET descricao=? WHERE id=?", (nova_desc.strip(), id_))
                                conn.commit()
                                conn.close()
                                st.session_state[f"editando_{id_}"] = False
                                st.success("Ocorrência alterada com sucesso!")
                                st.experimental_rerun()
                            else:
                                st.warning("Descrição não pode ficar vazia.")
                    with col_cancelar:
                        if st.button("❌ Cancelar", key=f"cancel_{id_}"):
                            st.session_state[f"editando_{id_}"] = False
                            st.experimental_rerun()
    else:
        st.info("Nenhuma ocorrência registrada.")

# ===== Página: Exportar Relatórios =====
def pagina_exportar():
    st.header("Exportar Relatório de Ocorrências 📄")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT cgm, nome, data, descricao, telefone FROM ocorrencias ORDER BY nome, data")
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        st.warning("Nenhuma ocorrência para exportar.")
        return

    opcao_export = st.radio("Escolha o tipo de exportação:", ["Relatório Completo", "Por Aluno Específico"])

    # Função para gerar PDF
    def gerar_pdf(caminho_pdf, ocorrencias):
        c = canvas.Canvas(caminho_pdf, pagesize=A4)
        desenhar_cabecalho_pdf(c)
        y = 700
        for cgm, nome, data, desc, telefone in ocorrencias:
            texto = f"CGM: {cgm}\nNome: {nome}\nData: {data}\nTelefone: {telefone}\nDescrição: {desc}\n----------------------"
            for linha in texto.split('\n'):
                c.drawString(50, y, linha)
                y -= 15
                if y < 80:
                    c.showPage()
                    desenhar_cabecalho_pdf(c)
                    y = 700
        y -= 30
        c.drawString(50, y, "Assinatura do Servidor: ____________________________")
        y -= 20
        c.drawString(50, y, "Assinatura do Responsável: ____________________________")
        y -= 20
        c.drawString(50, y, "Data: ____/____/______")
        c.save()

    if opcao_export == "Por Aluno Específico":
        alunos_com_ocorrencias = list(set([(cgm, nome) for cgm, nome, _, _, _ in resultados]))
        alunos_nomes = [f"{nome} (CGM: {cgm})" for cgm, nome in alunos_com_ocorrencias]
        if alunos_nomes:
            aluno_selecionado = st.selectbox("Selecione o aluno:", alunos_nomes)
            cgm_sel = aluno_selecionado.split("CGM: ")[1].replace(")", "")
            nome_sel = aluno_selecionado.split(" (CGM:")[0]
            ocorrencias_aluno = [r for r in resultados if r[0] == cgm_sel]

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📄 Exportar Word"):
                    doc = Document()
                    try:
                        doc.add_picture("CABEÇARIOAPP.png", width=doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin)
                    except:
                        pass
                    doc.add_heading(f"Relatório de Ocorrências - {nome_sel}", 0)
                    for cgm, nome, data, desc, telefone in ocorrencias_aluno:
                        doc.add_paragraph(f"CGM: {cgm}\nNome: {nome}\nData: {data}\nTelefone: {telefone}\nDescrição: {desc}\n----------------------")
                    doc.add_paragraph("\n\nAssinatura do Servidor: ____________________________\nAssinatura do Responsável: ____________________________\nData: ____/____/______")
                    caminho_word = f"relatorio_{nome_sel.replace(' ', '_')}.docx"
                    doc.save(caminho_word)
                    with open(caminho_word, "rb") as f:
                        st.download_button("📥 Baixar Word", f, file_name=caminho_word)

            with col2:
                if st.button("📄 Exportar PDF"):
                    caminho_pdf = f"relatorio_{nome_sel.replace(' ', '_')}.pdf"
                    gerar_pdf(caminho_pdf, ocorrencias_aluno)
                    with open(caminho_pdf, "rb") as f:
                        st.download_button("📥 Baixar PDF", f, file_name=caminho_pdf)

            with col3:
                if st.button("📱 Enviar WhatsApp"):
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("SELECT telefone FROM alunos WHERE cgm=?", (cgm_sel,))
                    tel_result = cursor.fetchone()
                    conn.close()
                    if tel_result and tel_result[0]:
                        telefone_aluno = tel_result[0]
                        mensagem = formatar_mensagem_whatsapp(ocorrencias_aluno, nome_sel)
                        st.text_area("Preview da mensagem:", mensagem, height=200)
                        numero = telefone_aluno.translate(str.maketrans("", "", "()- "))
                        mensagem_encoded = urllib.parse.quote(mensagem)
                        link_whatsapp = f"https://api.whatsapp.com/send?phone=55{numero}&text={mensagem_encoded}"
                        st.markdown(f"[👉 Enviar WhatsApp para {telefone_aluno}]({link_whatsapp})")
                    else:
                        st.warning("Telefone não cadastrado para este aluno.")

    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Exportar Word Completo"):
                doc = Document()
                try:
                    doc.add_picture("CABEÇARIOAPP.png", width=doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin)
                except:
                    pass
                doc.add_heading("Relatório Completo de Ocorrências", 0)
                for cgm, nome, data, desc, telefone in resultados:
                    doc.add_paragraph(f"CGM: {cgm}\nNome: {nome}\nData: {data}\nTelefone: {telefone}\nDescrição: {desc}\n----------------------")
                doc.add_paragraph("\n\nAssinatura do Servidor: ____________________________\nAssinatura do Responsável: ____________________________\nData: ____/____/______")
                caminho_word = "relatorio_ocorrencias.docx"
                doc.save(caminho_word)
                with open(caminho_word, "rb") as f:
                    st.download_button("📥 Baixar Word", f, file_name=caminho_word)

        with col2:
            if st.button("📄 Exportar PDF Completo"):
                caminho_pdf = "relatorio_ocorrencias.pdf"
                gerar_pdf(caminho_pdf, resultados)
                with open(caminho_pdf, "rb") as f:
                    st.download_button("📥 Baixar PDF", f, file_name=caminho_pdf)

# ===== Login =====
def login():
    st.title("Login 👤")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario.strip(), senha.strip()))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            st.session_state['logado'] = True
            st.session_state['usuario'] = usuario.strip()
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos!")

# ===== Menu =====
def menu():
    st.sidebar.image("BRASÃO.png", width=150)
    opcoes = ["Cadastro de Alunos", "Ocorrências", "Exportar Relatórios", "Cadastro de Usuário", "Lista de Alunos"]
    escolha = st.sidebar.selectbox("Menu", opcoes)
    if escolha == "Cadastro de Alunos":
        pagina_cadastro_alunos()
    elif escolha == "Ocorrências":
        pagina_ocorrencias()
    elif escolha == "Exportar Relatórios":
        pagina_exportar()
    elif escolha == "Cadastro de Usuário":
        pagina_cadastro_usuario()
    elif escolha == "Lista de Alunos":
        pagina_lista_alunos()

# ===== Execução =====
