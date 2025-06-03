import hashlib
import os

CHUNK_SIZE = 1024 * 1024  # 1MB modificar

def calculate_checksum(data):
    """ Calcula o checksum SHA-256 de um bloco de dados """
    return hashlib.sha256(data).hexdigest()

def compute_file_checksum(file_name):
    """ Calcula o checksum SHA-256 de um arquivo inteiro """
    with open(file_name, "rb") as f:
        data = f.read()
    return calculate_checksum(data)

def split_file(file_name):
    """
    Divide um arquivo em chunks de 1MB, calcula seus checksums e atribui um identificador único para cada bloco.
    Cada chunk é identificado por um número sequencial (index) utilizado também no nome do arquivo do chunk.
    Retorna uma lista de tuplas: (chunk_id, chunk_name, checksum)
    """
    chunks = []
    if not os.path.exists(file_name):
        return chunks

    with open(file_name, "rb") as f:
        index = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            checksum = calculate_checksum(chunk)
            chunk_name = f"{file_name}.chunk{index}"
            with open(chunk_name, "wb") as chunk_file:
                chunk_file.write(chunk)
            chunks.append((index, chunk_name, checksum))
            index += 1
    
    return chunks

def register_chunks(usuario_logado):
    """
    Registra os chunks de um arquivo no tracker.
    Cada chunk é uma tupla (chunk_id, chunk_name, checksum).
    O checksum final do arquivo (se calculado) também é enviado.
    """
    dados = {
        "action": "register_chunks",
        "username": usuario_logado,
        "chunk" : chunks
    }
    #egister_chunks(usuario_logado, file_name, chunks, file_checksum)
    print(f"Chunks do arquivo '{file_name}' registrados no tracker (por {usuario_logado}).")

def assemble_file(original_file_name, output_file=None):
    """
    Reconstroi o arquivo original a partir dos seus chunks.
    Procura por arquivos no formato '{original_file_name}.chunkX' e os une na ordem.
    """
    if output_file is None:
        output_file = f"{original_file_name}.assembled"
    index = 0
    with open(output_file, "wb") as outfile:
        while True:
            chunk_file = f"{original_file_name}.chunk{index}"
            if not os.path.exists(chunk_file):
                break
            with open(chunk_file, "rb") as infile:
                outfile.write(infile.read())
            index += 1
    print(f"Arquivo reassemblado como {output_file}.")