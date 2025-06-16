import json

def recolherChecksum(dados, nome_arquivo):
    if nome_arquivo not in dados:
        print(f"Arquivo {nome_arquivo} não encontrado nos dados.")
        return [], None

    info_arquivo = dados[nome_arquivo]
    checksum = info_arquivo.get("checksum")

    return checksum

# Carrega os dados do JSON primeiro
caminho = "arquivos_cadastrados/arquivos_tracker.json"
with open(caminho, "r", encoding="utf-8") as f:
    dados_json = json.load(f)

# Agora sim, passa os dados para a função
checksum = recolherChecksum(dados_json, "testeAnuncio.txt")
print("Checksum:", checksum)
