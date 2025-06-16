import os
import json


def carregar_peers_com_chunks(caminho_json, meu_username):
    if not os.path.exists(caminho_json):
        return []

    with open(caminho_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    chunks_do_usuario = []
    for info_arquivo in dados.values():
        donos = info_arquivo.get('donos', [])
        if meu_username in donos:
            chunks = info_arquivo.get('chunks', [])
            chunks_do_usuario.extend(chunks)

    return chunks_do_usuario
meu_username = "F"
caminho_json_chunks = "arquivos_cadastrados/arquivos_tracker.json"
chunks_disponiveis = carregar_peers_com_chunks(caminho_json_chunks, meu_username)
print(chunks_disponiveis)