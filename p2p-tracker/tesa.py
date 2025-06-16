import os
import json
import hashlib
import re

def carregar_peers_com_chunks(caminho_json, meu_username):
    """
    Carrega os chunks que pertencem ao usuário atual a partir de um JSON.

    Args:
        caminho_json (str): Caminho para o arquivo JSON contendo os dados dos arquivos.
        meu_username (str): Nome do usuário atual.

    Returns:
        list: Lista dos nomes dos chunks pertencentes ao usuário.
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
#meu_username = "F"
#caminho_json_chunks = "arquivos_cadastrados/arquivos_tracker.json"
#chunks_disponiveis = carregar_peers_com_chunks(caminho_json_chunks, meu_username)
#print(chunks_disponiveis)

import os


def montar_arquivo(caminho_pasta_chunks):
    """
    Reconstrói um arquivo original a partir de seus chunks localizados em uma pasta.

    Args:
        caminho_pasta_chunks (str): Caminho até a pasta contendo os chunks.
    """
    def calcular_checksum_arquivo(caminho_arquivo, algoritmo='sha256'):
        h = hashlib.new(algoritmo)
        with open(caminho_arquivo, 'rb') as f:
            while True:
                bloco = f.read(4096)
                if not bloco:
                    break
                h.update(bloco)
        return h.hexdigest()
    if not os.path.exists(caminho_pasta_chunks):
        print("Pasta dos chunks não existe!")
        return

    # Listar todos os chunks (arquivos) na pasta
    arquivos_chunks = [f for f in os.listdir(caminho_pasta_chunks) if os.path.isfile(os.path.join(caminho_pasta_chunks, f))]

    if not arquivos_chunks:
        print("Nenhum chunk encontrado na pasta.")
        return

    # Extrair nome base do arquivo, assumindo padrão nome.partX
    # Exemplo: "arquivo.part0" -> base = "arquivo"
    padrao = re.compile(r"(.+)\.part(\d+)$")

    # Montar lista de tuplas (indice, nome_arquivo)
    chunks_ordenados = []
    base_nome = ''
    for arquivo in arquivos_chunks:
        m = padrao.match(arquivo)
        if m:
            base_nome = m.group(1)
            indice = int(m.group(2))
            chunks_ordenados.append((indice, arquivo))
        else:
            print(f"Aviso: arquivo '{arquivo}' não segue o padrão esperado e será ignorado.")

    if not chunks_ordenados:
        print("Nenhum chunk válido encontrado para montagem.")
        return

    # Ordenar os chunks pelo índice
    chunks_ordenados.sort(key=lambda x: x[0])

    nome_arquivo_final = base_nome  # Usar o nome base sem extensão .partX
    checksum_local = calcular_checksum_arquivo(caminho_arquivo_final)
    checksum_esperado = requisitar_checksum_arquivo(
        host_do_tracker, porta_do_tracker, user, dono_original, nome_arquivo_final
    )

    caminho_arquivo_final = os.path.join("arquivos_montados", nome_arquivo_final)

    os.makedirs("arquivos_montados", exist_ok=True)

    # Abrir arquivo final para escrita em binário
    with open(caminho_arquivo_final, "wb") as f_saida:
        for idx, nome_chunk in chunks_ordenados:
            caminho_chunk = os.path.join(caminho_pasta_chunks, nome_chunk)
            with open(caminho_chunk, "rb") as f_chunk:
                dados = f_chunk.read()
                f_saida.write(dados)
            print(f"Chunk {nome_chunk} ({idx}) adicionado ao arquivo final.")

    print(f"Arquivo '{nome_arquivo_final}' montado com sucesso em '{caminho_arquivo_final}'!")

def escolher_pasta_para_montar(caminho_base="chunks_recebidos"):
    """
    Permite ao usuário escolher interativamente uma subpasta para montar o arquivo.

    Args:
        caminho_base (str): Caminho base onde estão as subpastas com os chunks.

    Returns:
        str | None: Caminho completo da pasta escolhida ou None se houver erro.
    """
    # Verifica se a pasta base existe
    if not os.path.exists(caminho_base):
        print(f"Pasta '{caminho_base}' não existe.")
        return None

    # Lista apenas as subpastas dentro do caminho_base
    subpastas = [f for f in os.listdir(caminho_base) if os.path.isdir(os.path.join(caminho_base, f))]

    if not subpastas:
        print(f"Nenhuma pasta encontrada dentro de '{caminho_base}'.")
        return None

    print("Pastas disponíveis para montar o arquivo:")
    for idx, pasta in enumerate(subpastas, 1):
        print(f"[{idx}] - {pasta}")

    while True:
        escolha = input("Digite o número da pasta que deseja montar: ")
        if escolha.isdigit():
            escolha_int = int(escolha)
            if 1 <= escolha_int <= len(subpastas):
                pasta_escolhida = subpastas[escolha_int - 1]
                print(f"Você escolheu: {pasta_escolhida}")
                return os.path.join(caminho_base, pasta_escolhida)
        print("Opção inválida. Tente novamente.")
# Exemplo de uso dentro do seu código
#if operation == "13":
user = "A"
caminho_pasta = escolher_pasta_para_montar("chunks_recebidos")
if caminho_pasta:
    print(f"Preparando para montar os chunks da pasta: {caminho_pasta}")
    # Aqui você chama a função que monta o arquivo a partir dos chunks nessa pasta
    montar_arquivo(caminho_pasta)
input("Pressione Enter para continuar")
os.system('cls||clear')
