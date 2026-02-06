import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# ==============================
# FUNÇÕES AUXILIARES
# ==============================

def normalizar_coluna(col):
    return (
        col.strip()
        .lower()
        .replace(" ", "_")
        .replace("ç", "c")
        .replace("ã", "a")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )

def get_col(row, *nomes):
    for nome in nomes:
        if nome in row and pd.notna(row[nome]):
            return str(row[nome]).strip()
    return ""

# ==============================
# LÓGICA DE CONVERSÃO
# ==============================

def converter():
    if not arquivo_path.get():
        messagebox.showwarning("Atenção", "Selecione um arquivo primeiro.")
        return

    delimitador = delimitadores[delimitador_var.get()]

    try:
        df = pd.read_csv(arquivo_path.get(), delimiter=delimitador, dtype=str)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler o arquivo:\n{e}")
        return

    df.columns = [normalizar_coluna(c) for c in df.columns]

    linhas_convertidas = []

    for idx, row in df.iterrows():
        cgm = get_col(row, "cgm")
        nome = get_col(row, "nome", "nome_do_estudante")
        telefone = get_col(row, "telefone", "fone", "celular")
        turma = get_col(row, "turma", "classe")
        data = get_col(row, "data", "data_nascimento", "nascimento")
        responsavel = get_col(row, "responsavel", "responsavel_legal", "pai_mae")

        if not cgm or not nome:
            continue

        linhas_convertidas.append({
            "cgm": cgm,
            "nome": nome,
            "telefone": telefone,
            "turma": turma,
            "data": data,
            "responsavel": responsavel
        })

    if not linhas_convertidas:
        messagebox.showwarning("Aviso", "Nenhum aluno válido encontrado.")
        return

    df_final = pd.DataFrame(
        linhas_convertidas,
        columns=["cgm", "nome", "telefone", "turma", "data", "responsavel"]
    )

    pasta = os.path.dirname(arquivo_path.get())
    saida = os.path.join(pasta, "alunos_convertido.txt")

    try:
       df_final.to_csv(
        saida,
        sep="\t",
        index=False,
        encoding="utf-8-sig",
        lineterminator="\r\n"
    )

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{e}")
        return

    messagebox.showinfo(
        "Sucesso",
        f"Conversão finalizada!\n\nArquivo gerado:\n{saida}\n\nTotal de alunos: {len(df_final)}"
    )

# ==============================
# INTERFACE GRÁFICA
# ==============================

root = tk.Tk()
root.title("Conversor de Alunos - TXT / CSV")
root.geometry("460x240")
root.resizable(False, False)
