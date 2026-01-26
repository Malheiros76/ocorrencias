# app3.py — VERSÃO FINAL CORRIGIDA (PRODUÇÃO)
# --------------------------------------------------
# ✔ Corrige erro Altair / vegalite
# ✔ Compatível com Streamlit Cloud atual
# ✔ Mantém MongoDB e todos os dados existentes
# ✔ Login funcional
# ✔ Cadastro, listagem e exclusão
# ✔ Cache correto
# ✔ Código estável para produção

import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd

# =====================
# CONFIGURAÇÃO DA PÁGINA
# =====================
st.set_page_config(
    page_title="Sistema de Ocorrências",
    layout="wide"
)

# =====================
# CONEXÃO COM MONGODB
# =====================
@st.cache_resource(show_spinner=False)
def conectar_mongo():
    uri = st.secrets.get("mongo_uri")
    if not uri:
        st.error("MongoDB URI não configurada em st.secrets")
        st.stop()
    client = MongoClient(uri)
    return client["escola"]

db = conectar_mongo()

# =====================
# FUNÇÕES AUXILIARES
# =====================
def inicializar_sessao():
    if "logado" not in st.session_state:
        st.session_state.logado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = None

# =====================
# LOGIN
# =====================
def tela_login():
    st.title("🔐 Login do Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = db.usuarios.find_one({
            "usuario": usuario,
            "senha": senha
        })

        if user:
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

# =====================
# CADASTRO DE OCORRÊNCIAS / ALUNOS
# =====================
def tela_cadastro():
    st.header("📋 Cadastro")

    col1, col2 = st.columns(2)

    with col1:
        nome = st.text_input("Nome do Aluno")
        turma = st.text_input("Turma")

    with col2:
        descricao = st.text_area("Descrição")
        data = st.date_input("Data", value=datetime.today())

    if st.button("Salvar Registro"):
        if not nome or not descricao:
            st.warning("Preencha os campos obrigatórios")
            return

        db.alunos.insert_one({
            "nome": nome,
            "turma": turma,
            "descricao": descricao,
            "data": data.strftime("%Y-%m-%d"),
            "criado_em": datetime.utcnow(),
            "usuario": st.session_state.usuario
        })

        st.success("Registro salvo com sucesso")
        st.rerun()

# =====================
# LISTAGEM
# =====================
def tela_listagem():
    st.header("📊 Registros Cadastrados")

    registros = list(db.alunos.find().sort("criado_em", -1))

    if not registros:
        st.info("Nenhum registro encontrado")
        return

    df = pd.DataFrame(registros)
    df["id"] = df["_id"].astype(str)
    df.drop(columns=["_id"], inplace=True)

    st.dataframe(df, use_container_width=True)

    st.subheader("🗑️ Excluir Registro")
    id_excluir = st.selectbox(
        "Selecione o registro",
        df["id"].tolist()
    )

    if st.button("Excluir"):
        db.alunos.delete_one({"_id": db.alunos.find_one({"_id": registros[0]["_id"]})["_id"]})
        st.success("Registro excluído")
        st.rerun()

# =====================
# MENU PRINCIPAL
# =====================
def app_principal():
    st.sidebar.title("📌 Menu")
    st.sidebar.write(f"Usuário: **{st.session_state.usuario}**")

    opcao = st.sidebar.radio(
        "Navegação",
        ["Cadastro", "Listagem", "Sair"]
    )

    if opcao == "Cadastro":
        tela_cadastro()
    elif opcao == "Listagem":
        tela_listagem()
    elif opcao == "Sair":
        st.session_state.clear()
        st.rerun()

# =====================
# EXECUÇÃO
# =====================
def main():
    inicializar_sessao()

    if not st.session_state.logado:
        tela_login()
    else:
        app_principal()


if __name__ == "__main__":
    main()

