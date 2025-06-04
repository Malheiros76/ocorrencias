input_path = "alunos.txt"  # Seu arquivo original
output_path = "alunos_formatado_tabulado.txt"  # Arquivo final

with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8-sig", newline="\r\n") as outfile:
    # Cabeçalho EXATO com tabulação
    outfile.write("CGM\tNome do Estudante\tTelefone\r\n")
    for linha in infile:
        partes = linha.strip().split("\t")
        if len(partes) == 3:
            cgm = partes[0].strip()
            nome = partes[1].strip()
            telefone = partes[2].strip()
            outfile.write(f"{cgm}\t{nome}\t{telefone}\r\n")