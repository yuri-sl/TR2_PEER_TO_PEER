import os
import json

def registrar_dono_no_json_arquivo(nome_arquivo: str, novo_dono: str):
    nome_arquivo_sem_extensao = os.path.splitext(nome_arquivo)[0]
    caminho = None

    for pasta_usuario in os.listdir("arquivos_cadastrados/chunkscriados"):
        possivel_caminho = f"arquivos_cadastrados/chunkscriados/{pasta_usuario}/{nome_arquivo_sem_extensao}/{nome_arquivo_sem_extensao}.json"
        if os.path.exists(possivel_caminho):
            caminho = possivel_caminho
            print("[SUCESSO] Encontrei o caminho:", caminho)
            break

    if caminho is None:
        print("[WARN] Arquivo JSON do chunk não encontrado para registrar dono.")
        return

    with open(caminho, 'r+', encoding='utf-8') as f:
        dados = json.load(f)
        modificado = False

        for chunk in dados:
            if chunk["nome"] == nome_arquivo:
                detentores = chunk.get("detentores_chunk", [])
                if novo_dono not in detentores:
                    detentores.append(novo_dono)
                    chunk["detentores_chunk"] = detentores
                    chunk["numero_detentores"] = len(detentores)
                    modificado = True
                    print(f"[SUCESSO] {novo_dono} adicionado como detentor de {nome_arquivo}")
                else:
                    print(f"[INFO] {novo_dono} já era detentor de {nome_arquivo}")
                break
        else:
            print(f"[ERRO] Chunk com nome '{nome_arquivo}' não encontrado no JSON.")

        if modificado:
            f.seek(0)
            json.dump(dados, f, indent=4)
            f.truncate()

# Exemplo de uso:
#registrar_dono_no_json_arquivo("TransferOne.part0", "A")
def atualizar_detentores_online_em_todos():
    path_base = "arquivos_cadastrados/chunkscriados"

    try:
        with open("usuarios_online.json", "r", encoding="utf-8") as f:
            print("Carreguei os usuários online")
            usuarios_online = set(json.load(f))
            print("Usuários online:", usuarios_online)
    except Exception as e:
        print(f"[ERRO] Erro ao carregar usuarios_online.json: {e}")
        return

    for usuario in os.listdir(path_base):
        caminho_usuario = os.path.join(path_base, usuario)
        if not os.path.isdir(caminho_usuario):
            continue

        for nome_pasta in os.listdir(caminho_usuario):
            caminho_subpasta = os.path.join(caminho_usuario, nome_pasta)
            if not os.path.isdir(caminho_subpasta):
                continue

            for nome_arquivo in os.listdir(caminho_subpasta):
                if not nome_arquivo.endswith(".json"):
                    continue

                caminho_json = os.path.join(caminho_subpasta, nome_arquivo)
                try:
                    with open(caminho_json, "r", encoding="utf-8") as f:
                        chunks_info = json.load(f)
                        print(f"\n[INFO] Processando: {caminho_json}")

                    for chunk in chunks_info:
                        detentores = chunk.get("detentores_chunk", [])
                        chunk["detentores_online"] = [p for p in detentores if p in usuarios_online]
                        chunk["quantidade_detentores_online"] = len(chunk["detentores_online"])

                    with open(caminho_json, "w", encoding="utf-8") as f:
                        json.dump(chunks_info, f, indent=4)

                    print(f"[SUCESSO] Atualizado com sucesso: {caminho_json}")

                except Exception as e:
                    print(f"[ERRO] Erro ao processar {caminho_json}: {e}")
atualizar_detentores_online_em_todos()