import os
import json

def listarArquivos(caminho_json="arquivos_cadastrados/arquivos_tracker.json"):
    if not os.path.exists(caminho_json):
        print("Arquivo JSON não encontrado!")
        return [], []

    with open(caminho_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    arquivos_disponiveis = []
    for nome_arquivo in dados.keys():
        if nome_arquivo.endswith('.txt'):
            arquivos_disponiveis.append(nome_arquivo)

    return arquivos_disponiveis, dados

def listar_chunks_do_arquivo(dados, nome_arquivo):
    if nome_arquivo not in dados:
        print(f"Arquivo {nome_arquivo} não encontrado nos dados.")
        return []

    info_arquivo = dados[nome_arquivo]
    chunks = info_arquivo.get('chunks', [])
    return chunks


caminho = "arquivos_cadastrados/arquivos_tracker.json"
arquivos, dados = listarArquivos(caminho)

if not arquivos:
    print("Nenhum arquivo .txt disponível encontrado.")
else:
    print("Arquivos disponíveis:")
    for i, nome in enumerate(arquivos):
        print(f"[{i}] - {nome}")

    try:
        escolha = int(input("Digite o número do arquivo que deseja selecionar: "))
        if 0 <= escolha < len(arquivos):
            nome_escolhido = arquivos[escolha]
            print(f"\nVocê escolheu o arquivo: {nome_escolhido}")

            # Após escolha do arquivo...
            chunks = listar_chunks_do_arquivo(dados, nome_escolhido)

            if not chunks:
                print("Nenhum chunk disponível para esse arquivo.")
            else:
                print("Chunks disponíveis para este arquivo:")
                # Se chunks forem strings:
                if isinstance(chunks[0], str):
                    for idx, chunk_nome in enumerate(chunks):
                        print(f"[{idx}] - {chunk_nome}")
                # Se chunks forem dicionários:
                else:
                    for idx, chunk in enumerate(chunks):
                        print(f"[{idx}] - {chunk['nome']} (checksum: {chunk.get('checksum', 'N/A')})")
                        print({chunk['nome']})
                        print({chunk['checksum']})
    except ValueError:
        print("Entrada inválida. Digite um número.")






