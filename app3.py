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

# Função de conexão
def conectar():
    return sqlite3.connect("ocorrencias.db", check_same_thread=False)

# Criar as tabelas se não existirem
def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            cgm TEXT PRIMARY KEY,
            nome TEXT,
            telefone TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cgm TEXT,
            nome TEXT,
            telefone TEXT,
            responsável TEXT,
            data TEXT,
            turma TEXT,
            descricao TEXT
        )
    """)

    conn.commit()
    conn.close()

# Login
def login():
    st.title("Login 👤")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            st.session_state['logado'] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")
            
# Função para formatar mensagem WhatsApp
def formatar_mensagem_whatsapp(ocorrencias_aluno, nome_aluno):
    """Formata as ocorrências de um aluno específico para envio via WhatsApp"""
    mensagem = f"📋 *RELATÓRIO DE OCORRÊNCIAS*\n"
    mensagem += f"👤 *Aluno:* {nome_aluno}\n"
    mensagem += f"📅 *Data do Relatório:* {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n"
    mensagem += "="*30 + "\n\n"
    
    for i, (cgm, nome, data, desc, telefone) in enumerate(ocorrencias_aluno, 1):
        # Formatar data para exibição
        try:
            data_formatada = datetime.strptime(data, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y às %H:%M")
        except:
            data_formatada = data
            
        mensagem += f"🔸 *Ocorrência {i}*\n"
        mensagem += f"📅 Data: {data_formatada}\n"
        mensagem += f"📝 Descrição: {desc}\n"
        mensagem += "-"*25 + "\n\n"
    
    mensagem += "👨‍🏫 *Escola [CCM Profº Luiz Carlos de Paula e Souza ]*\n"
    mensagem += "📞 Contato: [41 3348-4165]\n\n"
    mensagem += "_Este relatório foi gerado automaticamente pelo Sistema de Ocorrências._"
    
    return mensagem

# Aba: Cadastro de Alunos
def pagina_cadastro_alunos():
    st.header("Cadastro de Alunos 👦👧")

    cgm = st.text_input("CGM")
    nome = st.text_input("Nome")
    data_nascimento = st.date_input("Data de Nascimento")
    telefone = st.text_input("Telefone")
    responsavel = st.text_input("Responsável")
    data = st.date_input("Data de Cadastro")
    turma = st.text_input("Turma")


    if st.button("Salvar Aluno"):
        if cgm and nome:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (cgm, nome, telefone))
            conn.commit()
            conn.close()
            st.success("Aluno salvo com sucesso!")
        else:
            st.warning("Preencha pelo menos o CGM e o Nome.")

    # Importar via TXT
    st.subheader("Importar Alunos via TXT")
    arquivo_txt = st.file_uploader("Escolha o arquivo TXT", type=["txt"])
    if arquivo_txt is not None:
        df = pd.read_csv(arquivo_txt, sep=",", header=None, names=["CGM", "Nome", "Telefone"])
        st.dataframe(df)
        if st.button("Importar Alunos do TXT"):
            conn = conectar()
            cursor = conn.cursor()
            for index, row in df.iterrows():
                cursor.execute("INSERT OR REPLACE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (row["CGM"], row["Nome"], row["Telefone"]))
            conn.commit()
            conn.close()
            st.success("Importação concluída!")

# Aba: Cadastro de Usuários
def pagina_cadastro_usuario():
    st.header("Cadastro de Usuário 🧑‍💼")
    nome = st.text_input("Nome completo")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    setor = st.text_input("Setor")

    if st.button("Cadastrar Usuário"):
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO usuarios (nome, usuario, senha, setor)
                VALUES (?, ?, ?, ?)
            """, (nome, usuario, senha, setor))
            conn.commit()
            st.success("Usuário cadastrado!")
        except sqlite3.IntegrityError:
            st.error("Usuário já existe!")
        finally:
            conn.close()

# Aba: Lista de Alunos
def pagina_lista_alunos():
    st.header(" 📄 Lista de Alunos (Ordem Alfabética)")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT cgm, nome, telefone FROM alunos ORDER BY nome ASC")
    alunos = cursor.fetchall()
    conn.close()

    if alunos:
        df = pd.DataFrame(alunos, columns=["CGM", "Nome", "Telefone"])
        st.dataframe(df)
    else:
        st.warning("Nenhum aluno cadastrado.")

def pagina_ocorrencias():
    st.header("Registro de Ocorrências 📋 ")

    cgm_busca = st.text_input("CGM do aluno")
    nome, telefone = "", ""
    if cgm_busca:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, telefone FROM alunos WHERE cgm=?", (cgm_busca,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            nome, telefone = resultado
            st.info(f"Nome: {nome} | Telefone: {telefone}")

    descricao = st.text_area("Descrição da Ocorrência")

    if st.button("Salvar Ocorrência"):
        if cgm_busca and descricao:
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ocorrencias (cgm, nome, telefone, data, descricao)
                VALUES (?, ?, ?, ?, ?)
            """, (cgm_busca, nome, telefone, data_atual, descricao))
            conn.commit()
            conn.close()
            st.success("Ocorrência salva!")
            st.experimental_rerun()
        else:
            st.warning("Preencha CGM e descrição.")

    # Listar ocorrências
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, cgm, nome, data, descricao FROM ocorrencias ORDER BY data DESC")
    ocorrencias = cursor.fetchall()
    conn.close()

    if ocorrencias:
        st.subheader("📋 Ocorrências Registradas")
        
        for id, cgm, nome, data, desc in ocorrencias:
            with st.expander(f"{id} - {nome} ({cgm}) - {data}"):
                st.write("**Descrição atual:**")
                st.write(desc)
                
                # Botões de ação
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"✏️ Alterar {id}", key=f"alt_{id}"):
                        st.session_state[f"editando_{id}"] = True
                        st.rerun()
                
                with col2:
                    if st.button(f"🗑️ Excluir {id}", key=f"del_{id}"):
                        conn = conectar()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM ocorrencias WHERE id=?", (id,))
                        conn.commit()
                        conn.close()
                        st.success("Ocorrência excluída!")
                        st.rerun()
                
                # Formulário de edição
                if st.session_state.get(f"editando_{id}", False):
                    st.markdown("---")
                    st.write("**✏️ Editando Ocorrência:**")
                    
                    nova_descricao = st.text_area(
                        "Nova descrição:", 
                        value=desc, 
                        key=f"nova_desc_{id}",
                        height=100
                    )
                    
                    col_salvar, col_cancelar = st.columns(2)
                    
                    with col_salvar:
                        if st.button(f"💾 Salvar", key=f"save_{id}"):
                            if nova_descricao.strip():
                                conn = conectar()
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE ocorrencias SET descricao=? WHERE id=?", 
                                    (nova_descricao.strip(), id)
                                )
                                conn.commit()
                                conn.close()
                                
                                # Limpar estado de edição
                                st.session_state[f"editando_{id}"] = False
                                st.success("Ocorrência alterada com sucesso!")
                                st.rerun()
                            else:
                                st.warning("A descrição não pode estar vazia!")
                    
                    with col_cancelar:
                        if st.button(f"❌ Cancelar", key=f"cancel_{id}"):
                            st.session_state[f"editando_{id}"] = False
                            st.rerun()
    else:
        st.info("Nenhuma ocorrência registrada ainda.")
# Aba: Exportar Relatórios
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

    # Opção para escolher exportação
    opcao_export = st.radio(
        "Escolha o tipo de exportação:",
        ["Relatório Completo", "Por Aluno Específico"]
    )

    if opcao_export == "Por Aluno Específico":
        # Obter lista de alunos com ocorrências
        alunos_com_ocorrencias = list(set([(cgm, nome) for cgm, nome, _, _, _ in resultados]))
        alunos_nomes = [f"{nome} (CGM: {cgm})" for cgm, nome in alunos_com_ocorrencias]
        
        if alunos_nomes:
            aluno_selecionado = st.selectbox("Selecione o aluno:", alunos_nomes)
            cgm_selecionado = aluno_selecionado.split("CGM: ")[1].replace(")", "")
            nome_selecionado = aluno_selecionado.split(" (CGM:")[0]
            
            # Filtrar ocorrências do aluno selecionado
            ocorrencias_aluno = [r for r in resultados if r[0] == cgm_selecionado]
            
            # Botões de exportação para aluno específico
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Word"):
                    doc = Document()
                    try:
                        doc.add_picture("CABEÇARIOAPP.png", width=doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin)
                    except:
                        pass
                    doc.add_heading(f"Relatório de Ocorrências - {nome_selecionado}", 0)
                    
                    for cgm, nome, data, desc, telefone in ocorrencias_aluno:
                        doc.add_paragraph(f"CGM: {cgm}\nNome: {nome}\nData: {data}\nTelefone: {telefone}\nDescrição: {desc}\n----------------------")
                    
                    doc.add_paragraph("\n\nAssinatura do Servidor: ____________________________\nAssinatura do Responsável: ____________________________\nData: ____/____/______")
                    caminho_word = f"relatorio_{nome_selecionado.replace(' ', '_')}.docx"
                    doc.save(caminho_word)
                    
                    with open(caminho_word, "rb") as f:
                        st.download_button("📥 Baixar Word", f, file_name=caminho_word)
            
            with col2:
                if st.button("📄 PDF"):
                    caminho_pdf = f"relatorio_{nome_selecionado.replace(' ', '_')}.pdf"
                    c = canvas.Canvas(caminho_pdf, pagesize=A4)
                    
                    try:
                        logo = ImageReader("CABEÇARIOAPP.png")
                        c.drawImage(logo, 50, 750, width=500, preserveAspectRatio=True)
                    except:
                        pass
                    
                    y = 700
                    c.drawString(50, y, f"Relatório de Ocorrências - {nome_selecionado}")
                    y -= 30
                    
                    for cgm, nome, data, desc, telefone in ocorrencias_aluno:
                        texto = f"CGM: {cgm}\nNome: {nome}\nData: {data}\nTelefone: {telefone}\nDescrição: {desc}\n----------------------\n"
                        for linha in texto.split('\n'):
                            c.drawString(50, y, linha)
                            y -= 15
                            if y < 80:
                                c.showPage()
                                try:
                                    c.drawImage(logo, 50, 750, width=500, preserveAspectRatio=True)
                                except:
                                    pass
                                y = 700
                    
                    # Área de assinatura
                    y -= 30
                    c.drawString(50, y, "Assinatura do Servidor: ____________________________")
                    y -= 20
                    c.drawString(50, y, "Assinatura do Responsável: ____________________________")
                    y -= 20
                    c.drawString(50, y, "Data: ____/____/______")
                    c.save()
                    
                    with open(caminho_pdf, "rb") as f:
                        st.download_button("📥 Baixar PDF", f, file_name=caminho_pdf)
            
            with col3:
                if st.button("📱 WhatsApp"):
                    # Obter telefone do aluno
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("SELECT telefone FROM alunos WHERE cgm=?", (cgm_selecionado,))
                    tel_result = cursor.fetchone()
                    conn.close()
                    
                    if tel_result and tel_result[0]:
                        telefone_aluno = tel_result[0]
                        mensagem = formatar_mensagem_whatsapp(ocorrencias_aluno, nome_selecionado)
                        
                        # Mostrar preview da mensagem
                        with st.expander("📱 Preview da Mensagem WhatsApp"):
                            st.text(mensagem)
                        
                        numero = telefone_aluno.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
                        mensagem_encoded = urllib.parse.quote(mensagem)
                        link_whatsapp = f"https://api.whatsapp.com/send?phone=55{numero}&text={mensagem_encoded}"
                        
                        st.markdown(f"[👉 Enviar Relatório via WhatsApp para {telefone_aluno}]({link_whatsapp})")
                    else:
                        st.warning("Telefone não cadastrado para este aluno.")

    else:
        # Exportação completa (código original)
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Exportar para Word"):
                doc = Document()
                try:
                    doc.add_picture("CABEÇARIOAPP.png", width=doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin)
                except:
                    pass
                doc.add_heading("Relatório de Ocorrências", 0)
                for cgm, nome, data, desc, telefone in resultados:
                    doc.add_paragraph(f"CGM: {cgm}\nNome: {nome}\nData: {data}\nTelefone: {telefone}\nDescrição: {desc}\n----------------------")
                doc.add_paragraph("\n\nAssinatura do Servidor: ____________________________\nAssinatura do Responsável: ____________________________\nData: ____/____/______")
                caminho_word = "relatorio_ocorrencias.docx"
                doc.save(caminho_word)
                with open(caminho_word, "rb") as f:
                    st.download_button("📥 Baixar Word", f, file_name=caminho_word)

        with col2:
            if st.button("📄 Exportar para PDF"):
                caminho_pdf = "relatorio_ocorrencias.pdf"
                c = canvas.Canvas(caminho_pdf, pagesize=A4)
                try:
                    logo = ImageReader("CABEÇARIOAPP.png")
                    c.drawImage(logo, 50, 750, width=500, preserveAspectRatio=True)
                except:
                    pass
                y = 700
                for cgm, nome, data, desc, telefone in resultados:
                    texto = f"CGM: {cgm}\nNome: {nome}\nData: {data}\nTelefone: {telefone}\nDescrição: {desc}\n----------------------\n"
                    for linha in texto.split('\n'):
                        c.drawString(50, y, linha)
                        y -= 15
                        if y < 80:
                            c.showPage()
                            try:
                                c.drawImage(logo, 50, 750, width=500, preserveAspectRatio=True)
                            except:
                                pass
                            y = 700
                # Área de assinatura
                y -= 30
                c.drawString(50, y, "Assinatura do Servidor: ____________________________")
                y -= 20
                c.drawString(50, y, "Assinatura do Responsável: ____________________________")
                y -= 20
                c.drawString(50, y, "Data: ____/____/______")
                c.save()
                with open(caminho_pdf, "rb") as f:
                    st.download_button("📥 Baixar PDF", f, file_name=caminho_pdf)

        # Seção para envio via WhatsApp por aluno
        st.subheader("📱 Envio via WhatsApp")
        
        # Agrupar ocorrências por aluno
        ocorrencias_por_aluno = {}
        for cgm, nome, data, desc, telefone in resultados:
            if nome not in ocorrencias_por_aluno:
                ocorrencias_por_aluno[nome] = []
            ocorrencias_por_aluno[nome].append((cgm, nome, data, desc, telefone))
        
        for nome_aluno, ocorrencias_aluno in ocorrencias_por_aluno.items():
            with st.expander(f"📱 WhatsApp - {nome_aluno}"):
                # Obter telefone do primeiro registro (todos devem ser iguais)
                telefone_aluno = ocorrencias_aluno[0][4]
                
                if telefone_aluno:
                    mensagem = formatar_mensagem_whatsapp(ocorrencias_aluno, nome_aluno)
                    
                    # Preview da mensagem
                    st.text_area("Preview da mensagem:", mensagem, height=200, key=f"preview_{nome_aluno}")
                    
                    numero = telefone_aluno.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
                    mensagem_encoded = urllib.parse.quote(mensagem)
                    link_whatsapp = f"https://api.whatsapp.com/send?phone=55{numero}&text={mensagem_encoded}"
                    
                    st.markdown(f"[👉 Enviar para {telefone_aluno}]({link_whatsapp})")
                else:
                    st.warning("Telefone não disponível para este aluno.")

# Login
def login():
    st.title("Login 👤")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            st.session_state['logado'] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")



# Menu principal
def menu():
    st.sidebar.image("BRASÃO.png", width=200)
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
    elif menu == "Backup Manual":
        botao_backup_manual()

# Execução
if "logado" not in st.session_state:
    st.session_state["logado"] = False

inicializar_db()

if not st.session_state["logado"]:
    login()
else:
    menu()
