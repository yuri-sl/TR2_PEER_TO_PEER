import json

def obter_checksum(caminho_arquivo_json, nome_arquivo):
    with open(caminho_arquivo_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    if nome_arquivo in dados and "checksum" in dados[nome_arquivo]:
        return dados[nome_arquivo]["checksum"]
    else:
        return None
caminho = "arquivos_cadastrados/arquivos_tracker.json"
nome_arquivo = "Upload.txt"

checksum = obter_checksum(caminho, nome_arquivo)

if checksum:
    print("Checksum encontrado:", checksum)
else:
    print("Arquivo ou checksum não encontrado.")
