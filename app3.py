import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import base64
import io

# Configuração da página
st.set_page_config(page_title="Registro de Ocorrências", layout="wide")

# Função para colocar imagem de fundo (opcional)
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
            """, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

# Troque pelos seus arquivos ou remova essas duas linhas se não quiser fundo/imagem
set_background("fundo.png")
st.image("brasao.png", width=200)

# Conexão com o banco SQLite
conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

# Criar tabelas se não existirem
c.execute('''CREATE TABLE IF NOT EXISTS alunos (
    cgm TEXT PRIMARY KEY,
    nome TEXT,
    telefone TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS ocorrencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cgm TEXT,
    nome TEXT,
    telefone TEXT,
    turma TEXT,
    ano TEXT,
    data TEXT,
    fatos TEXT,
    agente_aplicador TEXT
)''')

conn.commit()

# Funções úteis
def buscar_ocorrencias(cgm):
    df = pd.read_sql_query("SELECT * FROM ocorrencias WHERE cgm = ?", conn, params=(cgm,))
    return df

def buscar_aluno_por_cgm(cgm):
    df = pd.read_sql_query("SELECT * FROM alunos WHERE cgm = ?", conn, params=(cgm,))
    if not df.empty:
        return df.iloc[0].to_dict()
    else:
        return None

def atualizar_ocorrencia(id_, campo, valor):
    c.execute(f"UPDATE ocorrencias SET {campo} = ? WHERE id = ?", (valor, id_))
    conn.commit()

def deletar_ocorrencia(id_):
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (id_,))
    conn.commit()

def inserir_aluno(cgm, nome, telefone):
    try:
        c.execute("INSERT OR IGNORE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", (cgm, nome, telefone))
        conn.commit()
    except sqlite3.Error:
        pass

def importar_alunos_txt(file):
    content = file.read().decode('utf-8').splitlines()
    count = 0
    for line in content:
        parts = line.split('\t')
        if len(parts) >= 3:
            cgm, nome, telefone = parts[0].strip(), parts[1].strip(), parts[2].strip()
            inserir_aluno(cgm, nome, telefone)
            count += 1
    return count

# Interface com abas
abas = st.tabs([
    "📋 Registrar Ocorrência",
    "🔍 Consultar Ocorrências",
    "✏️ Editar Ocorrência",
    "📄 Exportar Ocorrência",
    "📥 Importar Alunos",
    "📚 Lista de Alunos"
])

# Aba 1: Registrar Ocorrência
with abas[0]:
    st.subheader("Registrar nova ocorrência")

    with st.form("form_ocorrencia"):
        cgm = st.text_input("CGM do aluno")
        aluno_info = buscar_aluno_por_cgm(cgm.strip()) if cgm else None
        nome = st.text_input("Nome do aluno", value=aluno_info["nome"] if aluno_info else "")
        telefone = st.text_input("Telefone do responsável", value=aluno_info["telefone"] if aluno_info else "")
        turma = st.text_input("Turma")
        ano = st.text_input("Ano")
        data_ocorrencia = st.date_input("Data da ocorrência", value=date.today())
        fatos = st.text_area("Fatos ocorridos")
        agente_aplicador = st.text_input("Agente Aplicador")

        if st.form_submit_button("Registrar"):
            if not cgm.strip():
                st.error("Preencha o CGM do aluno.")
            elif not nome.strip():
                st.error("Preencha o nome do aluno.")
            elif not agente_aplicador.strip():
                st.error("Preencha o nome do agente aplicador.")
            else:
                try:
                    c.execute('''INSERT INTO ocorrencias 
                                 (cgm, nome, telefone, turma, ano, data, fatos, agente_aplicador)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                              (cgm.strip(), nome.strip(), telefone.strip(), turma.strip(), ano.strip(), data_ocorrencia.isoformat(), fatos.strip(), agente_aplicador.strip()))
                    conn.commit()
                    inserir_aluno(cgm.strip(), nome.strip(), telefone.strip())
                    st.success("Ocorrência registrada com sucesso!")
                except sqlite3.Error as e:
                    st.error(f"Erro ao registrar ocorrência: {e}")

# Aba 2: Consultar Ocorrências
with abas[1]:
    st.subheader("Consultar ocorrências por CGM")
    cgm_consulta = st.text_input("Informe o CGM para consulta", key="consulta_cgm")
    if cgm_consulta:
        df = buscar_ocorrencias(cgm_consulta.strip())
        if not df.empty:
            df_display = df[["data", "turma", "ano", "fatos", "agente_aplicador"]].sort_values(by="data", ascending=False)
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("Nenhuma ocorrência encontrada para esse CGM.")

# Aba 3: Editar Ocorrência
with abas[2]:
    st.subheader("Editar / Excluir ocorrências")
    cgm_edicao = st.text_input("Informe o CGM para editar", key="edicao_cgm")
    if cgm_edicao:
        df = buscar_ocorrencias(cgm_edicao.strip())
        if not df.empty:
            for _, row in df.iterrows():
                with st.expander(f"ID {row['id']} - {row['data']} - {row['fatos'][:30]}..."):
                    novo_fato = st.text_area("Fatos", row["fatos"], key=f"fato_{row['id']}")
                    novo_aplicador = st.text_input("Agente aplicador", row.get("agente_aplicador", ""), key=f"agente_{row['id']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Salvar", key=f"salvar_{row['id']}"):
                            atualizar_ocorrencia(row['id'], "fatos", novo_fato.strip())
                            atualizar_ocorrencia(row['id'], "agente_aplicador", novo_aplicador.strip())
                            st.success("Atualizado com sucesso!")
                    with col2:
                        if st.button("Excluir", key=f"excluir_{row['id']}"):
                            deletar_ocorrencia(row['id'])
                            st.warning("Ocorrência excluída.")
        else:
            st.info("Nenhuma ocorrência encontrada para esse CGM.")

# Aba 4: Exportar Ocorrência
with abas[3]:
    st.subheader("Exportar ocorrências para CSV ou Excel")
    cgm_export = st.text_input("Informe o CGM para exportar", key="export_cgm")
    if cgm_export:
        df = buscar_ocorrencias(cgm_export.strip())
        if not df.empty:
            st.write(f"Ocorrências encontradas: {len(df)}")

            csv = df.to_csv(index=False).encode('utf-8')
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_data = excel_buffer.getvalue()

            st.download_button("Baixar CSV", csv, file_name=f"ocorrencias_{cgm_export.strip()}.csv", mime='text/csv')
            st.download_button("Baixar Excel", excel_data, file_name=f"ocorrencias_{cgm_export.strip()}.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            st.info("Nenhuma ocorrência para exportar.")

# Aba 5: Importar Alunos
with abas[4]:
    st.subheader("Importar alunos a partir de arquivo .txt")
    arquivo = st.file_uploader("Escolha o arquivo .txt com os dados (colunas: CGM, Nome, Telefone)", type=["txt"])
    if arquivo:
        qtd = importar_alunos_txt(arquivo)
        st.success(f"{qtd} alunos importados com sucesso.")

# Aba 6: Lista de Alunos
with abas[5]:
    st.subheader("Lista completa de alunos")
    df_alunos = pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)
    if not df_alunos.empty:
        st.dataframe(df_alunos, use_container_width=True)
    else:
        st.info("Nenhum aluno cadastrado.")
