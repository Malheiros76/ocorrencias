import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Configurações iniciais
st.set_page_config(page_title="Sistema de Registro de Ocorrências", layout="wide")

conn = sqlite3.connect("ocorrencias.db", check_same_thread=False)
c = conn.cursor()

# Criação das tabelas se não existirem
c.execute("""
CREATE TABLE IF NOT EXISTS ocorrencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cgm TEXT NOT NULL,
    data TEXT NOT NULL,
    fatos TEXT NOT NULL,
    agente_aplicador TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS alunos (
    cgm TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    telefone TEXT
)
""")

conn.commit()

# Funções auxiliares

def buscar_ocorrencias(cgm: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT id, cgm, data, fatos, agente_aplicador FROM ocorrencias WHERE cgm = ? ORDER BY data DESC", 
        conn, params=(cgm,)
    )
    return df

def atualizar_ocorrencia(id: int, campo: str, valor: str):
    c.execute(f"UPDATE ocorrencias SET {campo} = ? WHERE id = ?", (valor, id))
    conn.commit()

def deletar_ocorrencia(id: int):
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (id,))
    conn.commit()

def limpar_campos_consultar():
    st.session_state.cgm_busca = ""

def limpar_campos_editar():
    st.session_state.cgm_gestao = ""

def limpar_campos_exportar():
    st.session_state.cgm_export = ""
    st.session_state.data_ini = date.today()
    st.session_state.data_fim = date.today()

def importar_alunos(arquivo):
    if arquivo is not None:
        try:
            linhas = arquivo.read().decode("utf-8").splitlines()
            for linha in linhas[1:]:
                campos = linha.split("\t")
                if len(campos) >= 3:
                    cgm_arquivo = campos[0].strip()
                    nome_arquivo = campos[1].strip()
                    telefone_arquivo = campos[2].strip()
                    c.execute("INSERT OR IGNORE INTO alunos (cgm, nome, telefone) VALUES (?, ?, ?)", 
                              (cgm_arquivo, nome_arquivo, telefone_arquivo))
            conn.commit()
            st.success("Alunos importados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao importar arquivo: {e}")

# Interface Streamlit

st.title("Sistema de Registro de Ocorrências Escolares")

abas = st.tabs(["Registrar Ocorrência", "Consultar Ocorrências", "Editar Ocorrência", "Exportar Ocorrência", "Importar Alunos", "Lista de Alunos"])

# Aba 0 - Registrar Ocorrência (básica para completar)
with abas[0]:
    st.subheader("Registrar nova ocorrência")
    cgm = st.text_input("CGM do aluno", key="cgm_registrar")
    data = st.date_input("Data da ocorrência", value=date.today(), key="data_registrar")
    fatos = st.text_area("Descrição dos fatos", key="fatos_registrar")
    aplicador = st.text_input("Agente Aplicador", key="aplicador_registrar")
    
    if st.button("Registrar ocorrência"):
        if cgm and fatos:
            c.execute("INSERT INTO ocorrencias (cgm, data, fatos, agente_aplicador) VALUES (?, ?, ?, ?)", 
                      (cgm, data.strftime("%Y-%m-%d"), fatos, aplicador))
            conn.commit()
            st.success("Ocorrência registrada com sucesso!")
            # Limpar campos
            st.session_state.cgm_registrar = ""
            st.session_state.fatos_registrar = ""
            st.session_state.aplicador_registrar = ""
        else:
            st.warning("Preencha o CGM e os fatos da ocorrência.")

# Aba 1 - Consultar Ocorrências
with abas[1]:
    st.subheader("Consultar ocorrências")
    cgm_busca = st.text_input("Digite o CGM para buscar ocorrências", key="cgm_busca")
    st.button("Limpar", key="limpar_consultar", on_click=limpar_campos_consultar)
    
    if cgm_busca:
        ocorrencias = buscar_ocorrencias(cgm_busca)
        if not ocorrencias.empty:
            df = ocorrencias[["data", "fatos"]].copy()
            df.columns = ["Data", "Fatos"]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma ocorrência encontrada para este CGM.")

# Aba 2 - Editar Ocorrência
with abas[2]:
    st.subheader("Gerenciar Ocorrências")
    cgm_gestao = st.text_input("CGM para editar/excluir", key="cgm_gestao")
    st.button("Limpar", key="limpar_editar", on_click=limpar_campos_editar)

    if cgm_gestao:
        resultados = buscar_ocorrencias(cgm_gestao)
        if not resultados.empty:
            for _, row in resultados.iterrows():
                with st.expander(f"{row['data']} - {row['fatos'][:30]}..."):
                    edit_key = f"edit_{row['id']}"
                    aplicador_key = f"aplicador_{row['id']}"
                    novo_fato = st.text_area("Editar fatos", row['fatos'], key=edit_key)
                    novo_aplicador = st.text_input("Editar Agente Aplicador", row.get('agente_aplicador', ""), key=aplicador_key)
                    
                    def salvar_edicao(id_row=row['id'], fato=novo_fato, aplicador=novo_aplicador):
                        atualizar_ocorrencia(id_row, 'fatos', fato)
                        atualizar_ocorrencia(id_row, 'agente_aplicador', aplicador)
                        st.experimental_rerun()
                        
                    def excluir_ocorrencia_cb(id_row=row['id']):
                        deletar_ocorrencia(id_row)
                        st.experimental_rerun()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.button("Salvar edição", key=f"save_{row['id']}", on_click=salvar_edicao)
                    with col2:
                        st.button("🔚 Excluir", key=f"delete_{row['id']}", on_click=excluir_ocorrencia_cb)
        else:
            st.info("Nenhuma ocorrência encontrada para este CGM.")

# Aba 3 - Exportar Ocorrência
with abas[3]:
    st.subheader("Exportar para .docx por período")

    cgm_export = st.text_input("CGM para exportar", key="cgm_export")
    data_ini = st.date_input("Data inicial", value=date.today(), key="data_ini")
    data_fim = st.date_input("Data final", value=date.today(), key="data_fim")

    st.button("Limpar", key="limpar_exportar", on_click=limpar_campos_exportar)

    if cgm_export:
        dados = buscar_ocorrencias(cgm_export)
        if not dados.empty:
            dados["data"] = pd.to_datetime(dados["data"])
            filtrado = dados[(dados["data"] >= pd.to_datetime(data_ini)) & (dados["data"] <= pd.to_datetime(data_fim))]
            if not filtrado.empty:
                st.write(f"{len(filtrado)} ocorrências encontradas no período.")
                st.dataframe(filtrado[["data", "fatos"]], use_container_width=True)
                # Aqui você pode implementar exportação para .docx, PDF etc.
            else:
                st.warning("Nenhuma ocorrência no período informado.")

# Aba 4 - Importar Alunos
with abas[4]:
    st.subheader("Importar alunos via .txt")

    arquivo = st.file_uploader("Escolha o arquivo .txt com os dados dos alunos", type="txt")
    
    if st.button("Importar"):
        importar_alunos(arquivo)

    if st.button("Limpar", key="limpar_importar"):
        st.info("Para limpar o arquivo, remova manualmente no uploader.")

# Aba 5 - Lista de Alunos
with abas[5]:
    st.subheader("Lista de alunos cadastrados")
    alunos_df = pd.read_sql_query("SELECT * FROM alunos", conn)
    st.dataframe(alunos_df, use_container_width=True)
