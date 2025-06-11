import hashlib
import os
import json

def dividir_em_chunks(nome_arquivo, tamanho_chunk_kb=1024):
    tamanho_chunk = tamanho_chunk_kb * 1024
    chunks_info = []
    nome_pasta = os.path.splitext(nome_arquivo)[0]
    nome_arquivo_json = nome_pasta + '.json'
    caminho_pasta = f'chunkscriados/{nome_pasta}'

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

                chunks_info.append({
                    "nome": chunk_nome,
                    "indice": i,
                    "hash": chunk_hash
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
chunks = dividir_em_chunks("bigfile.txt", 1024)


#arquivo = 'documento.txt'
#nome_sem = os.path.splitext(arquivo)[0]
#print(nome_sem)