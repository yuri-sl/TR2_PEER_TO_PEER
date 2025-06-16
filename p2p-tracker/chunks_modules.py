import hashlib
import os
import json
def listar_chunks_do_arquivo(dados, nome_arquivo):
    """
    Retorna os chunks associados a um determinado arquivo, se existirem.

    Parâmetros:
        dados (dict): Dicionário contendo os dados dos arquivos.
        nome_arquivo (str): Nome do arquivo cujos chunks serão listados.

    Retorna:
        list: Lista de chunks ou lista vazia se não encontrado.
    """
    if nome_arquivo not in dados:
        print(f"Arquivo {nome_arquivo} não encontrado nos dados.")
        return []

    info_arquivo = dados[nome_arquivo]
    chunks = info_arquivo.get('chunks', [])
    return chunks

def calculate_checksum(data) -> str:
    """
    Calcula o checksum (SHA-256) de um dado binário.

    Parâmetros:
        data (bytes): Conteúdo em binário para o qual será calculado o checksum.

    Retorna:
        str: Hash SHA-256 em hexadecimal.
    """
    return hashlib.sha256(data).hexdigest()

def compute_file_checksum(arquivo) -> str:
    """
    Calcula o checksum (SHA-256) de um arquivo completo.

    Parâmetros:
        arquivo (str): Caminho do arquivo.

    Retorna:
        str: Hash SHA-256 do conteúdo do arquivo.
    """
    with open(arquivo, "rb") as a:
        data = a.read()
    return calculate_checksum(data)

def dividir_em_chunks(nome_arquivo, tamanho_chunk_kb=1024,usuario_logado: str=""):
    """
    Divide um arquivo em chunks e salva cada um deles em disco. 
    Cria também um arquivo JSON com os metadados dos chunks.

    Parâmetros:
        nome_arquivo (str): Caminho do arquivo a ser dividido.
        tamanho_chunk_kb (int): Tamanho de cada chunk em kilobytes (KB). Padrão: 1024.
        usuario_logado (str): Nome do usuário que está dividindo o arquivo.

    Retorna:
        list|None: Lista com informações dos chunks ou None se houve erro.
    """
    tamanho_chunk = tamanho_chunk_kb * 1024
    chunks_info = []
    detentores_chunk = []
    detentores_chunk.append(usuario_logado)
    nome_pasta = os.path.splitext(nome_arquivo)[0]
    nome_arquivo_json = nome_pasta + '.json'
    caminho_pasta = f'arquivos_cadastrados/chunkscriados/{nome_pasta}'

    if os.path.exists(caminho_pasta):
        print("O arquivo já está dividido em chunks!")
        return None

    try:
        os.mkdir(caminho_pasta)
        with open(nome_arquivo, 'rb') as f:
            i = 0
            while True:
                dados = f.read(tamanho_chunk)
                if not dados:
                    break
                chunk_nome = f"{nome_pasta}.part{i}"
                caminho_chunk = os.path.join(caminho_pasta, chunk_nome)

                with open(caminho_chunk, 'wb') as chunk_file:
                    chunk_file.write(dados)

                chunk_hash = hashlib.sha256(dados).hexdigest()
                checksum = calculate_checksum(dados)

                chunks_info.append({
                    "nome": chunk_nome,
                    "indice": i,
                    "hash": chunk_hash,
                    "checksum":checksum,
                    "detentores_chunk":detentores_chunk
                })
                i += 1

        with open(os.path.join(caminho_pasta, nome_arquivo_json), 'w') as jf:
            json.dump(chunks_info, jf, indent=4)

        print(f"{len(chunks_info)} chunks criados com sucesso.")
        return chunks_info

    except Exception as e:
        print(f"Erro ao dividir arquivo: {e}")
        return None

# Exemplo de uso
chunks = dividir_em_chunks("testingChunksUpdate50.txt", 1024,"A")

def dividir_em_chunks_user(nome_arquivo, tamanho_chunk_kb=1024,usuario_logado: str=""):
    """
    Variante de dividir_em_chunks que armazena os chunks em uma pasta por usuário.

    Parâmetros:
        nome_arquivo (str): Caminho do arquivo a ser dividido.
        tamanho_chunk_kb (int): Tamanho de cada chunk em kilobytes (KB).
        usuario_logado (str): Nome do usuário dono dos chunks.

    Retorna:
        list|None: Lista de dicionários com dados dos chunks ou None se erro.
    """
    tamanho_chunk = tamanho_chunk_kb * 1024
    chunks_info = []
    detentores_chunk = []
    detentores_chunk.append(usuario_logado)
    nome_pasta = os.path.splitext(nome_arquivo)[0]
    nome_arquivo_json = nome_pasta + '.json'
    caminho_pasta = f'arquivos_cadastrados/chunkscriados/{usuario_logado}/{nome_pasta}'

    if os.path.exists(caminho_pasta):
        print("O arquivo já está dividido em chunks!")
        return None

    try:
        os.makedirs(caminho_pasta)
        with open(nome_arquivo, 'rb') as f:
            i = 0
            while True:
                dados = f.read(tamanho_chunk)
                if not dados:
                    break
                chunk_nome = f"{nome_pasta}.part{i}"
                caminho_chunk = os.path.join(caminho_pasta, chunk_nome)

                with open(caminho_chunk, 'wb') as chunk_file:
                    chunk_file.write(dados)

                chunk_hash = hashlib.sha256(dados).hexdigest()
                checksum = calculate_checksum(dados)

                chunks_info.append({
                    "nome": chunk_nome,
                    "indice": i,
                    "hash": chunk_hash,
                    "checksum":checksum,
                    "detentores_chunk":detentores_chunk
                })
                i += 1

        with open(os.path.join(caminho_pasta, nome_arquivo_json), 'w') as jf:
            json.dump(chunks_info, jf, indent=4)

        print(f"{len(chunks_info)} chunks criados com sucesso.")
        return chunks_info

    except Exception as e:
        print(f"Erro ao dividir arquivo: {e}")
        return None

# Exemplo de uso
chunks = dividir_em_chunks_user("testeAnuncio2.txt", 1024,"A")


#arquivo = 'documento.txt'
#nome_sem = os.path.splitext(arquivo)[0]
#print(nome_sem)