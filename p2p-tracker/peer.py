import hashlib
import os

CHUNK_SIZE = 1024 * 1024  # 1MB modificar

def calculate_checksum(data) -> str:
    """ Calcula o checksum SHA-256 de um bloco de dados """
    return hashlib.sha256(data).hexdigest()

def compute_file_checksum(arquivo) -> str:
    """ Calcula o checksum SHA-256 de um arquivo inteiro """
    with open(arquivo, "rb") as a:
        data = a.read()
    return calculate_checksum(data)

def split_file(arquivo):
    """
    Divide um arquivo em chunks de 1MB, calcula seus checksums e atribui um identificador único para cada bloco.
    Cada chunk é identificado por um número sequencial (index) utilizado também no nome do arquivo do chunk.
    Retorna uma lista de tuplas: (chunk_id, chunk_name, checksum)
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
    Registra os chunks de um arquivo no tracker.
    Cada chunk é uma tupla (chunk_id, chunk_name, checksum, hash_chunk).
    O checksum final do arquivo (se calculado) também é enviado.
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

def assemble_file(original_file_name, chunk_dir="chunkscriados/", output_file=None) -> None:
    """
    Reconstrói o arquivo original a partir dos seus chunks.
    Procura por arquivos no formato '{original_file_name}.chunkX' dentro da pasta especificada.
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
    else:
        print(f"Nenhum chunk encontrado para '{original_file_name}' na pasta '{chunk_dir}'.")

def pedir_chunks(chunk_desejado, usuario):
    pass