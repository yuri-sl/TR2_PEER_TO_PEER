import json

def recolherChecksum(dados, nome_arquivo):
    """
    Recupera o valor do checksum associado a um arquivo, a partir de um dicionário carregado de um JSON.

    Args:
        dados (dict): Dicionário com os dados carregados do arquivo JSON do tracker.
        nome_arquivo (str): Nome do arquivo cujo checksum se deseja obter.

    Returns:
        str | None: O valor do checksum se o arquivo existir nos dados, ou None caso contrário.
    """
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
