import os
import json

def carregar_peers_com_chunks(caminho_json, meu_username):
    """
    Carrega a lista de chunks que pertencem ao usuário especificado.

    Essa função lê um arquivo JSON contendo informações sobre os arquivos e seus donos.
    Ela retorna os nomes dos chunks que estão associados ao usuário atual.

    Args:
        caminho_json (str): Caminho para o arquivo JSON com os dados dos arquivos.
        meu_username (str): Nome do usuário atual, usado para filtrar os chunks.

    Returns:
        list: Lista com os nomes dos chunks pertencentes ao usuário.
    """
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

caminho_json_chunks = "arquivos_cadastrados/arquivos_tracker.json"
meu_username = "A"
chunks_disponiveis = carregar_peers_com_chunks(caminho_json_chunks, meu_username)
print(f"Os chunks disponiveis carregados para : {meu_username} foram {chunks_disponiveis}")