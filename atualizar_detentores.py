import os
import json

def atualizar_detentores_online_em_todos():
    path_base = "arquivos_cadastrados/chunkscriados"

    # Carrega os peers online
    try:
        with open("usuarios_online.json", "r") as f:
            print("Carreguei os usuários online")
            usuarios_online = set(json.load(f))
    except Exception as e:
        print(f"❌ Erro ao carregar usuarios_online.json: {e}")
        return

    # Percorre todas as pastas de usuários
    for usuario in os.listdir(path_base):
        caminho_usuario = os.path.join(path_base, usuario)
        if not os.path.isdir(caminho_usuario):
            continue

        # Dentro da pasta do usuário, percorre todos os arquivos (que são .json de cada arquivo anunciado)
        for nome_arquivo in os.listdir(caminho_usuario):
            if not nome_arquivo.endswith(".json"):
                continue

            caminho_json = os.path.join(caminho_usuario, nome_arquivo)
            try:
                with open(caminho_json, "r") as f:
                    chunks_info = json.load(f)

                for chunk in chunks_info:
                    detentores = chunk.get("detentores_chunk", [])
                    chunk["detentores_online"] = [p for p in detentores if p in usuarios_online]

                with open(caminho_json, "w") as f:
                    json.dump(chunks_info, f, indent=4)

                print(f"✅ Atualizado: {caminho_json}")

            except Exception as e:
                print(f"❌ Erro ao processar {caminho_json}: {e}")

# Executa a função
atualizar_detentores_online_em_todos()
