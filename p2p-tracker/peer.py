import hashlib
import os

CHUNK_SIZE = 1024 * 1024  # 1MB modificar

def calculate_checksum(data) -> str:
    """ Calcula o checksum SHA-256 de uma chunk"""
    return hashlib.sha256(data).hexdigest()

def compute_file_checksum(arquivo) -> str:
    """ Calcula o checksum SHA-256 de um arquivo todo"""
    with open(arquivo, "rb") as a:
        data = a.read()
    return calculate_checksum(data)

def split_file(arquivo):
    """
    Fragmenta um arquivo em blocos de 1KB, calcula o checksum SHA-256 de cada bloco e atribui um identificador único a eles.
    Cada bloco é numerado sequencialmente (index), o que também é usado para nomear o arquivo correspondente.
    Retorna uma lista de tuplas no formato: (chunk_id, nome_do_chunk, checksum).

    Retorna:
        list of (int, str, str): Uma lista de tuplas contendo (index, nome_do_chunk, checksum)
    """
    chunks = []
    output_dir = "chunkscriados"
    os.makedirs(output_dir, exist_ok=True)
    with open(arquivo, "rb") as a:
        index = 0
        while True:
            chunk = a.read(CHUNK_SIZE)
            if not chunk:
                break
            checksum = calculate_checksum(chunk)
            chunk_name = os.path.join(output_dir, f"{arquivo}.chunk{index}")
            with open(chunk_name, "wb") as chunk_file:
                chunk_file.write(chunk)
            chunks.append((index, chunk_name, checksum))# não consegui colocar o hash
            index += 1
    return chunks

def register_chunks(arquivos,usuario_logado) -> dict:
    """
    Registra os blocos (chunks) de um arquivo no tracker.
    Cada chunk é representado por uma tupla contendo: (chunk_id, nome_do_chunk, checksum, hash_chunk).
    Se o checksum final do arquivo for calculado, ele também será incluído no envio.
    
    Retorna:
        {
        "action": "register_chunks",
        "username": usuario_logado, -> str
        "chunk" : chunks -> list of (int, str, str)
        }
    """
    chunks = []
    for a in arquivos:
        chunks.append(split_file(a))
    dados = {
        "action": "register_chunks",
        "username": usuario_logado,
        "chunk" : chunks
    }
    return dados

def assemble_file(original_file_name, chunk_dir="chunkscriados/", output_file=None) -> str:
    """
    Reconstrói o arquivo original a partir dos seus blocos (chunks).
    Busca na pasta especificada por arquivos nomeados no formato: '{original_file_name}.chunkX'.
    """
    if output_file is None:
        output_file = f"{original_file_name}.txt.assembled"
    print(output_file)
    index = 0
    found_chunks = False

    with open(output_file, "wb") as outfile:
        while True:
            chunk_path = os.path.join(chunk_dir, f"{original_file_name}.txt.chunk{index}")
            if not os.path.exists(chunk_path):
                break
            with open(chunk_path, "rb") as infile:
                outfile.write(infile.read())
            found_chunks = True
            index += 1

    if found_chunks:
        print(f"Arquivo reassemblado como '{output_file}'.")
        return compute_file_checksum(output_file)
    else:
        print(f"Nenhum chunk encontrado para '{original_file_name}' na pasta '{chunk_dir}'.")
        return 0

def register_arquivos(arquivos,usuario_logado) -> list[str]:
    """
    Calcula o checksum de todos os arquivos
    """
    checksunsarq = []
    for a in arquivos:
        checksunsarq.append((a,compute_file_checksum(a)))
    dados = {
        "action": "register_arq",
        "username": usuario_logado,
        "checksunsarq" : checksunsarq
    }
    return dados

def pedir_chunks(chunk_desejado, usuario_logado):
    pass