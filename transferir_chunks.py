import json
import os

def get_missing_chunks(dados):
    if dados['action'] != "get_missing_chunks":
        return

    with open("arquivos_cadastrados/arquivos_tracker.json", "r") as f:
        tracker_data = json.load(f)

    arquivos_detalhados = {
        k: v for k, v in tracker_data.items() if isinstance(v, dict) and 'chunks' in v
    }

    total_missing_chunks = {}

    usuario_pedinte = dados['username']

    for nome_arquivo, info in arquivos_detalhados.items():
        chunks_path_tracker = os.path.dirname(info['chunks_path']) + "/"

        # Ignora os arquivos que o próprio peer anunciou
        if dados['created_path'] in chunks_path_tracker:
            continue

        # Caminho local dos chunks recebidos deste arquivo
        nome_arquivo_sem_extensao = nome_arquivo.split('.txt')[0]
        caminho_local_chunks = os.path.join("chunks_recebidos",usuario_pedinte, nome_arquivo_sem_extensao)
        print(f"O caminho local é: {caminho_local_chunks}")
        os.makedirs(caminho_local_chunks, exist_ok=True)
        chunks_locais = set(os.listdir(caminho_local_chunks))

        # Verifica quais chunks ainda faltam
        faltando = [
            chunk for chunk in info["chunks"]
            if chunk not in chunks_locais
        ]

        if faltando:
            total_missing_chunks[nome_arquivo] = faltando

    return total_missing_chunks


# Exemplo de uso
dados = {
    'action': "get_missing_chunks",
    'created_path': "arquivos_cadastrados/chunkscriados/A/",
    "username":"A"
}

faltantes = get_missing_chunks(dados)
print(json.dumps(faltantes, indent=2))
