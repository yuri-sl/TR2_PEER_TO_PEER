import queue
from tracker import *
import subprocess
import sys
import os
import socket
import json
import random
import platform
import shutil
import re
from datetime import datetime
from criar_arquivos import create_big_text_file
from acessarTrackerJson import listarArquivos,listar_chunks_do_arquivo
from peer_messages import *
import threading
from peer import *
from new_graph import plotarGraficoMultiplas,plotarGraficoSingle
import queue
import threading

menu_1 = "MENU PRINCIPAL \n#1 - Registrar;\n#2 - Login no Sistema;\n#3 - Sair do sistema;"
menu_2 = "\n4 - Anunciar um Arquivo;\n5 - Listagem de Peers Ativos;\n6 - Iniciar Chat com Peer;\n7 - Montar arquivo;\n8 - Anunciar arquivos manualmente;\n9 - Anunciar todos os chunks;\n10 - Sair do Sistema;\n11 - Criar um novo arquivo .txt\n12 - Requisição de Chunk\n13 - Montar arquivo usando chunks\n 14 - Próxima página >>>>"

menu_chats = "--Menu de interações de chats por usuários--(1/3)\n#5 - Listagem de peers Ativos\n#6 - Iniciar chat com um Peer\n\n#14 - Próxima página >>>>"
menu_arquivos = "--Menu de Operações por arquivos--(2/3)\n#11 - Criar um arquivo .txt\n#8 - Anunciar um arquivo manualmente\n#12 - Requisição de Chunks com uma conexão\n#16 - Requisição de chunks com múltiplas conexões\n#13 - Montar um Arquivo\n#17 - Plotar Gráfico Transmissão única\n#18 - Plotar Gráfico Transmissão Múltiplas Conexões\n#1 - Pedir arquivos\n\n#14 - Próxima página >>>>\n#15 - Página anterior <<<<<<"
menu_opcoes = "--Menu de operações do Usuário--(3/3)\n#14 - Meu perfil\n#10 - Sair do sistema\n\n#15 - Página anterior <<<<<<"

SCOREBOARD_FILE = "/scoreboard.json"
TRANSFER_METRICS_FILE = "transfer_metrics_single.json"
TRANSFER_METRICS_FILE_CONNECTIONS = "transfer_metrics_connections.json"
def verificar_chunks_faltantes(username, nome_arquivo):
    dados = {
        "action": "verify_missing_chunks",
        "username": username,
        "nome_arquivo": nome_arquivo
    }

    resposta = send_to_tracker(dados)

    if resposta.get("status") == "ok":
        print(f"\n🔍 Verificação de chunks faltantes para '{nome_arquivo}':")
        print(" - Chunks que você já possui:")
        for chunk in resposta.get("chunks_recebidos", []):
            print(f"   ✔ {chunk}")
        print(" - Chunks disponíveis em outros peers:")
        for chunk in resposta.get("chunks_disponiveis_outros_peers", []):
            print(f"    {chunk}")
        print(" - Chunks que ainda estão faltando:")
        for chunk in resposta.get("chunks_faltando", []):
            print(f"   [ERRO] {chunk}")
    else:
        print(f"[ERRO] Erro: {resposta.get('mensagem')}")

def listarUsuariosAtivos(usuario_logado):
    portAssociationCon = []
    dados = {
    "action": "list_clients",
    "username": usuario_logado
    }
    resposta = send_to_tracker(dados)
    print()
    print("Peers Ativos: ")
    for peer in resposta.get("mensagem", []):
        portAssociationCon.append(peer)
        if(peer == usuario_logado):
            print(f" - {peer} (Você)")
        else:
            print(f" - {peer}")
    return portAssociationCon
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
def get_bytes_score(peer_user):
    with open("scoreboard.json", "r") as f:
        scores = json.load(f)
    return scores.get(peer_user, {}).get("bytes_sent", 0)

def calcularPeersOnline(usuario_logado):
    peers_bleach_brave_souls = listarUsuariosAtivos(usuario_logado)
    dados = {
        "action":"update_user_list",
        "peers_online":peers_bleach_brave_souls,
        "username":usuario_logado
    }
    resposta = send_to_tracker(dados)
    print(resposta)

def get_transmisson_score(peer):
    with open("scoreboard.json", "r") as f:
        scores = json.load(f)
    s = scores.get(peer, {})
    return (
        s.get("bytes_sent", 0)
        + s.get("successful_responses", 0) * 10
        + s.get("tempo_conectado", 0) * 2
        - s.get("failed_transfers", 0) * 5
    )

def get_limite_conexoes(score):
    if score < 10:
        return 1
    elif score < 30:
        return 2
    elif score < 60:
        return 3
    else:
        return 4

def get_peer_info(peer_dono):
    dados_peer_info = {
        "action":"get_peer_info_chunk",
        "username": peer_dono
    }
    resposta_info = send_to_tracker(dados_peer_info)
    if resposta_info.get("status") == "ok":
        return resposta_info["mensagem"]
    return None


def baixar_chunks_em_paralelo(peer_ip, peer_port, usuario_logado, peer_user, chunks):
    """
    Inicia threads para baixar múltiplos chunks do mesmo peer em paralelo.
    """
    threads = []
    for chunk_nome in chunks:
        thread = threading.Thread(
            target=requisitar_chunk,
            args=(peer_ip, peer_port, usuario_logado, peer_user, chunk_nome)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
def load_transfer_metrics():
    if os.path.exists(TRANSFER_METRICS_FILE):
        try:
            with open(TRANSFER_METRICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("[WARN] Não foi possível carregar 'transfer_metrics_single.json'. Inicializando vazio.")
            return {}
    return {}

def save_transfer_metrics(data):
    with open(TRANSFER_METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def add_transfer_time(peer_id: str, transfer_time: float) -> None:
    """Armazena o tempo de transferência para o peer específico."""
    metrics = load_transfer_metrics()
    metrics.setdefault(peer_id, []).append(transfer_time)
    save_transfer_metrics(metrics)

def add_transfer_record(peer_id: str, tempo: float, volume: int, integridade: bool):
    """Adiciona um registro de transferência para o peer especificado."""
    metrics = load_transfer_metrics()
    if peer_id not in metrics:
        metrics[peer_id] = []
    metrics[peer_id].append({
        "tempo": tempo,
        "volume": volume,
        "integridade": integridade
    })
    save_transfer_metrics(metrics)


def load_transfer_metrics_Connections():
    if os.path.exists(TRANSFER_METRICS_FILE_CONNECTIONS):
        try:
            with open(TRANSFER_METRICS_FILE_CONNECTIONS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("[WARN] Não foi possível carregar 'transfer_metrics_single.json'. Inicializando vazio.")
            return {}
    return {}

def save_transfer_metrics_Connections(data):
    with open(TRANSFER_METRICS_FILE_CONNECTIONS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def add_transfer_time_Connections(peer_id: str, transfer_time: float) -> None:
    """Armazena o tempo de transferência para o peer específico."""
    metricsConnections = load_transfer_metrics_Connections()
    metricsConnections.setdefault(peer_id, []).append(transfer_time)
    save_transfer_metrics_Connections(metricsConnections)

def add_transfer_record_Connections(peer_id: str, tempo: float, volume: int, integridade: bool):
    """Adiciona um registro de transferência para o peer especificado."""
    metricsConnections = load_transfer_metrics_Connections()
    if peer_id not in metricsConnections:
        metricsConnections[peer_id] = []
    metricsConnections[peer_id].append({
        "tempo": tempo,
        "volume": volume,
        "integridade": integridade
    })
    save_transfer_metrics_Connections(metricsConnections)

checksum_arquivos = {}

CONEXOES_ABERTAS_FILE = "conexoes_abertas.json"

def load_conexoes_abertas():
    """Carrega o arquivo de conexões abertas, ou retorna estrutura vazia."""
    if os.path.exists(CONEXOES_ABERTAS_FILE):
        with open(CONEXOES_ABERTAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"conexoes": []}

def save_conexoes_abertas(data):
    """Salva as conexões abertas no arquivo JSON."""
    with open(CONEXOES_ABERTAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def registrar_conexao(user, port, chunk_name):
    """Registra uma conexão aberta para um peer e chunk específico."""
    data = load_conexoes_abertas()
    data["conexoes"].append({
        "user": user,
        "port": port,
        "chunk": chunk_name,
        "timestamp": datetime.now().isoformat()
    })
    save_conexoes_abertas(data)

def finalizar_conexao(user, port, chunk_name):
    """Remove uma conexão aberta quando finaliza."""
    data = load_conexoes_abertas()
    data["conexoes"] = [
        conn for conn in data["conexoes"]
        if not (conn["user"] == user and conn["port"] == port and conn["chunk"] == chunk_name)
    ]
    save_conexoes_abertas(data)

def quantas_conexoes_abertas():
    """Retorna o total atual de conexões abertas."""
    data = load_conexoes_abertas()
    return len(data["conexoes"])

def obter_checksum(caminho_arquivo_json, nome_arquivo):
    with open(caminho_arquivo_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    if nome_arquivo in dados and "checksum" in dados[nome_arquivo]:
        return dados[nome_arquivo]["checksum"]
    else:
        return None
def recolherChecksum(dados, nome_arquivo):
    """
    Recupera o checksum de um arquivo a partir de um dicionário de dados.

    Parâmetros:
        dados (dict): Dicionário contendo os dados dos arquivos.
        nome_arquivo (str): Nome do arquivo a ser verificado.

    Retorna:
        tuple: ([], None) se o arquivo não for encontrado, senão retorna apenas o checksum.
    """
    if nome_arquivo not in dados:
        print(f"Arquivo {nome_arquivo} não encontrado nos dados.")
        return [], None

    info_arquivo = dados[nome_arquivo]
    checksum = info_arquivo.get("checksum")

    return checksum

def montar_arquivo(caminho_pasta_chunks,usuarioLogado):
    """
    Reconstrói um arquivo completo a partir dos seus chunks salvos em uma pasta.

    Parâmetros:
        caminho_pasta_chunks (str): Caminho da pasta onde estão os chunks.
        usuarioLogado (str): Nome do usuário que irá receber o arquivo montado.
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
    def calcular_checksum_dados(dados_bytes, algoritmo='sha256'):
        h = hashlib.new(algoritmo)
        h.update(dados_bytes)
        return h.hexdigest()

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

    #caminho_arquivo_final = os.path.join("arquivos_montados", nome_arquivo_final)
    caminho_arquivo_final = "arquivos_motados/"+nome_arquivo_final

    print(f"o nome_arquivo_final é: {nome_arquivo_final}")

    for i, chunk in enumerate(chunks_ordenados):
        print(f"Chunk {i}: {chunk[0]}")


    nome_arquivo_final += ".txt"
    caminho_arquivo_final = f"arquivos_montados/{usuarioLogado}/{nome_arquivo_final}"
    os.makedirs(f"arquivos_montados/{usuarioLogado}", exist_ok=True)

    # [SUCESSO] VERIFICA SE ALGUM CHUNK ESTÁ FALTANDO
    chunks_faltando = []
    for idx, nome_chunk in chunks_ordenados:
        caminho_chunk = os.path.join(caminho_pasta_chunks, nome_chunk)
        if not os.path.exists(caminho_chunk):
            chunks_faltando.append(nome_chunk)

    if chunks_faltando:
        print("[ERRO] Não é possível montar o arquivo! Os seguintes chunks estão faltando:")
        for chunk in chunks_faltando:
            print(f" - {chunk}")
        return

    # [SUCESSO] VERIFICA SE O ARQUIVO JÁ FOI MONTADO
    if os.path.exists(caminho_arquivo_final):
        print(f"[WARN] O arquivo '{nome_arquivo_final}' já existe. Abortando montagem.")
        return

    # [SUCESSO] MONTA O ARQUIVO
    with open(caminho_arquivo_final, "wb") as f_saida:
        for idx, nome_chunk in chunks_ordenados:
            caminho_chunk = os.path.join(caminho_pasta_chunks, nome_chunk)
            with open(caminho_chunk, "rb") as f_chunk:
                dados = f_chunk.read()
                f_saida.write(dados)
            print(f"[SUCESSO] Chunk {nome_chunk} ({idx}) adicionado ao arquivo final.")

    print(f"[SUCESSO]Arquivo '{nome_arquivo_final}' montado com sucesso em '{caminho_arquivo_final}'!")

    with open(caminho_arquivo_final, "wb") as f_saida:
        for idx, nome_chunk in chunks_ordenados:
            caminho_chunk = os.path.join(caminho_pasta_chunks, nome_chunk)
            with open(caminho_chunk, "rb") as f_chunk:
                dados = f_chunk.read()
                f_saida.write(dados)
            print(f"Chunk {nome_chunk} ({idx}) adicionado ao arquivo final.")
    print(f"[SUCESSO] Arquivo '{nome_arquivo_final}' montado com sucesso em '{caminho_arquivo_final}'!")
    # Só agora calcula o checksum real
    checksum_local = calcular_checksum_arquivo(caminho_arquivo_final)
    checksumEsperado = obter_checksum("arquivos_cadastrados/arquivos_tracker.json", nome_arquivo_final)
    
    print("Checksum local     :", checksum_local)
    print("Checksum esperado  :", checksumEsperado)

    if checksum_local == checksumEsperado:
        print("[SUCESSO] Checksum válido! Transferência concluída.")
        os.makedirs("reports", exist_ok=True)
        with open("reports/transfer_report.txt", "a", encoding='utf-8') as report_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report_file.write(f"[{timestamp}][SUCESSO] Arquivo '{nome_arquivo_final}' montado com sucesso em '{caminho_arquivo_final}'!\n")
    else:
        print("[ERRO] Checksum inválido! O arquivo pode estar corrompido.")
        os.makedirs("reports", exist_ok=True)
        with open("reports/transfer_report.txt", "a", encoding='utf-8') as report_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report_file.write(f"{timestamp}[ERRO]CHECKSUM INVÁLIDO!! ARQUIVO NÃO FOI CONSTRUÍDO!\n")

    #else:
    #    print("CHECKSUM INVÁLIDO!! ARQUIVO NÃO FOI CONSTRUÍDO!")
    #    os.makedirs("reports", exist_ok=True)
    #    with open("reports/transfer_report.txt", "a", encoding='utf-8') as report_file:
    #        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #        report_file.write(f"{timestamp}[ERRO]CHECKSUM INVÁLIDO!! ARQUIVO NÃO FOI CONSTRUÍDO!")


def escolher_pasta_para_montar(caminho_base="chunks_recebidos"):
    """
    Lista as subpastas de uma pasta base e permite ao usuário escolher uma para montagem.

    Parâmetros:
        caminho_base (str): Caminho onde estão as pastas de chunks.

    Retorna:
        str|None: Caminho da pasta escolhida ou None se não houver pastas válidas.
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

def adicionar_dono_chunk(arquivo_json, nome_arquivo, novo_dono):
    """
    Adiciona um novo dono à lista de donos de um arquivo no arquivo JSON do tracker.

    Parâmetros:
        arquivo_json (str): Caminho do arquivo JSON contendo os dados dos arquivos.
        nome_arquivo (str): Nome do arquivo a ser atualizado.
        novo_dono (str): Nome do usuário a ser adicionado como dono.
    """
    if not os.path.exists(arquivo_json):
        print("Arquivo JSON de tracker não encontrado.")
        return

    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    if nome_arquivo not in dados:
        print(f"O arquivo {nome_arquivo} não está registrado no tracker.")
        return

    if "donos" not in dados[nome_arquivo]:
        dados[nome_arquivo]["donos"] = []

    if novo_dono not in dados[nome_arquivo]["donos"]:
        dados[nome_arquivo]["donos"].append(novo_dono)

        with open(arquivo_json, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

        print(f"[SUCESSO] Usuário '{novo_dono}' agora listado como dono de '{nome_arquivo}'.")
    else:
        print(f"[INFO] Usuário '{novo_dono}' já é dono de '{nome_arquivo}'.")

def salvar_transfer_record(data):
    """Salva o registro de transferência em transfer_records.json"""
    arquivo = "transfer_records.json"
    registros = []
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            try:
                registros = json.load(f)
            except json.JSONDecodeError:
                registros = []
    registros.append(data)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(registros, f, indent=4, ensure_ascii=False)

def requisitar_chunk(host, port,from_user, to_user, nome_chunk, inicio_download=0,single=True):
    """
    Envia um pedido de chunk para um peer específico via conexão TCP.

    Args:
        host (str): Endereço IP do peer destinatário.
        port (int): Porta TCP do peer destinatário.
        from_user (str) : Remetente
        to_user (str): Nome do usuário destinatário.
        nome_chunk (str): Nome do usuário remetente.
        text (str): Conteúdo da mensagem a ser enviada.

    O formato da mensagem enviada é um JSON contendo remetente, destinatário,
    texto da mensagem e timestamp do envio.
    """

    pedidos = {
        "from":from_user,
        "to":to_user,
        "nome_chunk":nome_chunk
    }
    scoreboard = load_scoreboard()
    config = get_peer_priority(to_user, scoreboard)
    
    while threads_ativas_para(to_user) >= config["max_conexoes"]:
        #print(f"Limite de conexões atingido para {to_user}. Aguardando...")
        time.sleep(1.5)

    adicionar_conexao(to_user)
    print("Json gerado!")
    #print(pedidos)
    print(f"A porta do host é: {port}")
    try:
        #inicio_download = time.time()
        start_time = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(f"Conexão bem-sucedida com {to_user} ({host}:{port}) [SUCESSO]")
        s.sendall(json.dumps(pedidos).encode())
        s.shutdown(socket.SHUT_WR)
        ttf = time.time() - start_time
        # Garante que a pasta de destino exista
        os.makedirs("chunks_recebidos", exist_ok=True)

        # Caminho completo do arquivo que será salvo
        caminho_arquivo = os.path.join("chunks_recebidos", nome_chunk)
        print(f"\n Requisição enviada para {to_user} ({host}:{port})[SUCESSO]\n")
        # Recebe os dados do chunk e grava no disco

        # Lê os primeiros 4 bytes que indicam o tamanho do JSON
        tamanho_bytes = s.recv(4)
        if len(tamanho_bytes) < 4:
            print("[ERRO] Não foi possível ler os 4 bytes do tamanho do JSON.")
            return False

        tamanho_json = int.from_bytes(tamanho_bytes, byteorder='big')
        print(f" Esperado tamanho do JSON: {tamanho_json} bytes")

        json_bytes = b''
        while len(json_bytes) < tamanho_json:
            parte = s.recv(tamanho_json - len(json_bytes))
            if not parte:
                print("[ERRO] Conexão encerrada antes de receber o JSON completo.")
                return False
            json_bytes += parte

        try:
            json_data = json.loads(json_bytes.decode())
        except json.JSONDecodeError as e:
            print(f"[ERRO] Erro ao decodificar JSON recebido: {e}")
            print(f"Conteúdo bruto recebido: {json_bytes}")
            return False
        # atualiza a pontuação daquele peer:
        #new_score = update_score(peer_id, bytes_sent=0,
        #                 time_connected=ttf,
        #                 successful_responses=successful)
        print("JSON recebido decodificado:", json_bytes.decode())
        print("json_data:", json_data)

        json_info = json_data[0]
        nome_chunk = json_info['nome']
        checksum_esperado = json_info['checksum']

        #Lê o chunk e armazena em memória temporariamente
        dados_recebidos = b''
        #Lendo o Chunk
        while True:
            dados = s.recv(config["largura_banda"])
            if not dados:
                break
            dados_recebidos += dados
            #print("Recebendo chunk...")

        #Calcula o Hash e verifica o checksum
        #print(dados_recebidos)
        checksum_recebido = hashlib.sha256(dados_recebidos).hexdigest()
        nome_diretorio = nome_chunk.split('.')[0]

        #print("O CHECKSUM RECEBIDO É:")

        if checksum_recebido == checksum_esperado:
            caminho_arquivo = "chunks_recebidos/"+from_user+"/"+nome_diretorio+"/"+nome_chunk
            os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)  # <-- CRIA diretórios se não existirem
            with open(caminho_arquivo,'wb') as f:
                f.write(dados_recebidos)
            fim_download = time.time()
            tempo_total = fim_download - inicio_download
            print(f"\n Chunk '{nome_chunk}' recebido de {to_user} e salvo em '{caminho_arquivo}'. [SUCESSO]\n")
            print(f"Checksum confirmado: {checksum_recebido}")
            print(f"O Tempo total de download: {tempo_total:.2f} segundos.")

            nome_diretorio = nome_chunk.split('.')[0]
            caminho_arquivo = os.path.join("chunks_recebidos", from_user, nome_diretorio, nome_chunk)

            # Verificação de integridade
            checksum_recebido = hashlib.sha256(dados_recebidos).hexdigest()
            integridade_ok = (checksum_recebido == checksum_esperado)


            if integridade_ok:
                os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
                with open(caminho_arquivo, 'wb') as f:
                    f.write(dados_recebidos)

                print(f"[SUCESSO] Chunk '{nome_chunk}' recebido e salvo em '{caminho_arquivo}'.")

            else:
                print(f"[ERRO] Checksum não bate para '{nome_chunk}': esperado {checksum_esperado}, recebido {checksum_recebido}")
                print(f"Esperado: {checksum_esperado}")
                print(f"Recebido: {checksum_recebido}")
            tempo_individual = time.time() - start_time
            volume = len(dados_recebidos)
            if single:
                add_transfer_record(from_user, tempo_individual, volume, integridade_ok)
            else:
                add_transfer_record_Connections(from_user, tempo_individual, volume, integridade_ok)

            # Salva registro em JSON
            registro = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "from_user": from_user,
                "to_user": to_user,
                "chunk_name": nome_chunk,
                "transfer_time": tempo_total,
                "checksum_match": integridade_ok,
                "bytes_transferred": len(dados_recebidos)
            }
            salvar_transfer_record(registro)

    except Exception as e:
        print(f"[ERRO] Erro ao requisitar chunk: {e}")

    finally:
        remover_conexao(to_user)
        s.close()                

def launch_tracker_cross_platform() -> None:
    """
    Executa o script 'tracker.py' em um novo terminal, de forma compatível com múltiplos sistemas operacionais.

    - No Windows: abre o 'cmd' com o script sendo executado via 'python'.
    - No Linux: tenta abrir um novo terminal com o script usando 'gnome-terminal', 'xterm' ou 'konsole'. 
      Caso nenhum desses terminais esteja disponível, executa o script diretamente em segundo plano.
    
    A saída de erro padrão é redirecionada para /dev/null (ignorada) em sistemas Linux.
    """
    null = subprocess.DEVNULL
    system = platform.system()
    if system == 'Windows':
        subprocess.Popen(['start', 'cmd', '/k', 'python tracker.py'], shell=True)
    elif system == 'Linux':
        if shutil.which('gnome-terminal'):
            subprocess.Popen(['gnome-terminal', '--', 'python3', 'tracker.py'], stderr=null)
        elif shutil.which('xterm'):
            subprocess.Popen(['xterm', '-hold', '-e', 'python3 tracker.py'], stderr=null)
        elif shutil.which('konsole'):
            subprocess.Popen(['konsole', '-e', 'python3 tracker.py'], stderr=null)
        else:
            subprocess.Popen(['python3', 'tracker.py'], stderr=null)

def send_to_tracker(data) -> dict:
    """
    Envia dados codificados em JSON para o tracker via socket TCP e aguarda uma resposta.

    Conecta-se ao tracker localizado em 'localhost' na porta 5000. Os dados enviados devem ser serializáveis em JSON.

    Após o envio completo, a função aguarda a resposta do tracker, que também deve estar em formato JSON.

    Retorna:
        dict: A resposta decodificada do tracker, convertida de JSON para dicionário Python.

    Em caso de falha de conexão (por exemplo, se o tracker não estiver em execução),
    imprime uma mensagem de erro e retorna um dicionário indicando a falha.

    Exemplo de retorno em caso de erro:
        {"status": "erro", "mensagem": "Tracker não disponível."}
    """
    HOST = 'localhost'
    PORT = 5000
    try:    
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((HOST,PORT))
        s.sendall(json.dumps(data).encode())
        s.shutdown(socket.SHUT_WR)  # Indica que terminou de enviar dados
        buffer = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buffer += chunk
        s.close()
        return json.loads(buffer.decode())
    except ConnectionRefusedError:
        print("Não foi possível iniciar o Tracker. ele já está ativo?")
        return {"status":"erro","mensagem":"Tracker não disponível."}
    
def start_heartbeat(username) -> None:
    """
    Inicia uma thread em segundo plano que envia um sinal de "heartbeat" periódico ao tracker.

    Após um breve atraso inicial (1 segundo), a thread envia continuamente uma requisição
    contendo o nome de usuário ao tracker para indicar que o cliente ainda está ativo.

    - Se o tracker responder com algo diferente de {"status": "ok"}, o cliente assume que foi desconectado por inatividade.
    - Em caso de falha de conexão ou resposta inválida, o cliente é encerrado imediatamente.

    O intervalo entre os heartbeats está configurado para 60 segundos.

    Parâmetros:
        username (str): Nome de usuário que será incluído nas mensagens de heartbeat.
    """
    def loop():
        time.sleep(1)  # <- aqui: espera o login ser processado no Tracker
        while True:
            try:
                dados = {"action": "heartbeat", "username": username}
                resposta = send_to_tracker(dados)
                if resposta.get("status") != "ok":
                    print("[WARN] Você foi desconectado por inatividade. Faça login novamente.")
                    os._exit(1)
                time.sleep(5)
            except:
                print("[WARN] Erro de conexão no heartbeat. Encerrando cliente.")
                os._exit(1)
    threading.Thread(target=loop, daemon=True).start()

def salvar_mensagem(usuario_remetente,destinatario,mensagem,caminho_arquivo = "messages_list.json") -> None:
    """
    Salva uma mensagem em um arquivo JSON contendo uma lista de mensagens.

    Cada mensagem é armazenada como um dicionário com os campos:
    - "usuario_remetente": remetente da mensagem,
    - "usuario_destinatario": destinatário da mensagem,
    - "mensagem": o conteúdo da mensagem.

    Caso o arquivo JSON já exista, a função carrega a lista atual de mensagens e adiciona a nova mensagem.
    Se o arquivo não existir, estiver vazio ou apresentar erro de formato, cria uma nova lista.

    Parâmetros:
        usuario_remetente (str): Nome do usuário que envia a mensagem.
        destinatario (str): Nome do usuário destinatário da mensagem.
        mensagem (str): Conteúdo da mensagem a ser salva.
        caminho_arquivo (str, opcional): Caminho do arquivo JSON onde as mensagens serão salvas. Padrão é "messages_list.json".

    Observações:
        - Se o arquivo apresentar conteúdo inválido, ele será sobrescrito com uma nova lista contendo a mensagem atual.
    """
    registro_mensagem = {
        "usuario_remetente":usuario_remetente,
        "usuario_destinatario":destinatario,
        "mensagem":mensagem
    }

    mensagens_salvas = []

    if os.path.exists(caminho_arquivo):
        try:
            f = open(caminho_arquivo,"r",encoding="utf-8")
            conteudo = f.read().strip()
            if conteudo:
                dados = json.loads(conteudo)
                if isinstance(dados,list):
                    mensagens_salvas = dados
                else:
                    print("Formato inválido detectado em messages_list.json. Substituindo por lista.")
            else:
                print("Arquivo vazio, criando nova lista de mensagens")
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}. Reiniciando arquivo.")
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}. Reiniciando arquivo.")
    mensagens_salvas.append(registro_mensagem)

    #f = open(caminho_arquivo,"w",encoding="utf-8")
    #json.dumps(mensagens_salvas,f,indent=4,ensure_ascii=False)

        

def is_tracker_running(host = 'localhost',port=5000) -> bool:
    """
    Verifica se o tracker está ativo e aceitando conexões na máquina e porta especificadas.

    Tenta abrir uma conexão TCP com o host e porta indicados.
    Se conseguir conectar, assume que o tracker está rodando e retorna True.
    Se a conexão for recusada, retorna False.

    Parâmetros:
        host (str): Endereço do servidor tracker (padrão 'localhost').
        port (int): Porta TCP do servidor tracker (padrão 5000).

    Retorna:
        bool: True se o tracker está rodando, False caso contrário.
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((host,port))
        s.close()
        return True
    except ConnectionRefusedError:
        return False

def interactiveMenu_1() -> bool:
    """
    Menu para o usuário
    """
    usuario_logado = None
    chat_port = 5000 + random.randint(1,1000)
    chunk_port = 5000 + random.randint(1,1000)
    os.system('cls||clear')
    menu_index = 0

    while True:
        os.system('cls||clear')
        print(menu_1)
        operation = input("insira a sua operação desejada:\n")

        if operation == "1":
            usernameRegister = input("Defina seu nome de usuário: ")
            passwordRegister = input("Defina a sua senha: ")
            confirm_password = input("Confirme a sua senha: ")
            if passwordRegister != confirm_password:
                print("Senhas não coincidiram!")
                input("Aperte Enter para continuar")
                continue
            print("Passou adiante!")
            dados = {
                "action": "register",
                "username": usernameRegister,
                "password": passwordRegister
            }
            print("JSon gerado!")
            resposta = send_to_tracker(dados)
            print("Chegou resposta!!")

            print(resposta["mensagem"])
            input("Pressione enter para continuar")
            os.system('cls||clear')

        elif operation == "2":
            username_login = input("Insira o seu nome de usuário: ")
            password = input("Insira sua senha: ")
            arquivos = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.txt')]
            dados = {
                "action": "login",
                "username": username_login,
                "password": password,
                "files"   : arquivos,
                "chat_port": chat_port,
                "chunk_port": chunk_port
            }
            resposta = send_to_tracker(dados)
            print("Resposta recebida!")
            #print(resposta)

            if resposta.get("status") == "ok":
                print(resposta["mensagem"])
                usuario_logado = username_login
                start_peer_server(chat_port,chunk_port,usuario_logado)
                start_heartbeat(usuario_logado)
                break  # break the first menu loop and go to the second
            if resposta.get("status") == "erro":
                print("Erro - ",resposta['mensagem'])
            input("Pressione enter para continuar")
            os.system('cls||clear')

        elif operation == "3":
            print("Bye Bye!!")
            exit()
            return False
        else:
            print("Operação inválida!")
            input("Pressione Enter para continuar")
            os.system('cls||clear')

    # Now you're logged in (usuario_logado is set)
    while usuario_logado:
        os.system('cls||clear') #Limpar o diretório
        calcularPeersOnline(usuario_logado)
        avaiable_menus = [menu_chats,menu_arquivos,menu_opcoes]
        active_menu = avaiable_menus[menu_index]
        print(active_menu)
        operation = input("insira a sua operação desejada:\n")

        if operation == "4":
            try:
                dados = {
                    "action": "list_files",
                    "username": usuario_logado
                }
                resposta = send_to_tracker(dados)
                print("Arquivos dos Peers Ativos: ")
                print(resposta["mensagem"])
                #print(files)
                input("Pressione Enter para continuar")
                os.system('cls||clear')
            except:
                print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")

        elif operation == "5":
            try:
                listarUsuariosAtivos(usuario_logado)
                input("Pressione Enter para continuar")
                os.system('cls||clear')              
            except:
                print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")
        elif operation == "6":
            try:
                print(chat_port)
                dados = {
                    "action": "list_clients",
                    "username": usuario_logado
                }
                resposta = send_to_tracker(dados)
                print()
                print("Peers Ativos: ")
                i = 0
                for peer in resposta.get("mensagem", []):
                    i += 1
                    if(peer == usuario_logado):
                        print(f"[{i}] - {peer} (Você)")
                    else:
                        print(f"[{i}] - {peer}")
                accept_chat = input(("Gostaria de comunicar com um Peer?\n1-Sim    0-Não\n"))
                if accept_chat == "1":
                    selected_user = input("Digite o nome do usuário que deseja falar com\n")
                    i = 0
                    for user in resposta.get("mensagem",[]):
                        i += 1
                        if selected_user == user or str(i) == selected_user:
                            print("Usuário Escolhido para conversar com sucesso!")
                            dados_start_chat = {
                                "action":"get_peer_info",
                                "username": user
                            }
                            resposta_start_chat = send_to_tracker(dados_start_chat)

                            if resposta_start_chat.get("status")=="ok":
                                peer_info = resposta_start_chat.get("mensagem",{})
                                peer_ip = peer_info.get("ip")
                                peer_port = peer_info.get("port")
                                print(f"Iniciando a conversa com {user} em {peer_ip}:{peer_port}")
                                print(f"Digite a sua mensagem para falar com {user}:")
                                texto = input("Digite sua mensagem:")
                                send_message_to_peer(peer_ip, peer_port, usuario_logado, user, texto)
                                #Escrevendo a mensagem em JSON

                                registro_mensagem = {
                                    "usuario_remetente":usuario_logado,
                                    "usuario_destino": user,
                                    "mensagem":texto
                                }
                                msgPath = "messages_list.json"

                                #Verifica se o arquivo já existe e carrega o interior dele
                                if os.path.exists(msgPath):
                                    print("Arquivo existe!")
                                    f = open(msgPath,"r",encoding="utf-8")
                                    recorded_messages = json.load(f)
                                else:
                                    recorded_messages = []
                                recorded_messages.append(registro_mensagem)
                                f = open(msgPath,"w",encoding="utf-8")
                                json.dump(recorded_messages,f,indent=4,ensure_ascii=False)
                            else:
                                print("Erro ao obter infos do User")
                            break
                    print("Este usuário não está online ou não existe!")
                
                input("Pressione Enter para continuar")
                os.system('cls||clear')
            except:
                #print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")
        elif operation == "7":
            #Montar Aquivo
            # Caminho da pasta com os chunks
            pasta_chunks = "chunkscriados"

            # Lista para guardar nomes únicos dos arquivos originais
            nomes_unicos = set()
            if os.path.isdir(pasta_chunks):
                # Percorre todos os arquivos da pasta
                for nome_arquivo in os.listdir(pasta_chunks):
                    if '.' in nome_arquivo:
                        nome_base = nome_arquivo.split('.')[0]  # pega antes do .index
                        nomes_unicos.add(nome_base)

            # Converte para lista se quiser usar como menu
            lista_arquivos = list(nomes_unicos)
            print("Arquivos disponíveis:")
            for i, nome in enumerate(lista_arquivos, start=1):
                print(f"[{i}] - {nome}")

            try:
                arquivo = int(input("Qual arquivo você quer juntar? "))
                arquivo -=1
                dados = {
                    "action": "reassembly",
                    "username": usuario_logado,
                    "arquivo" : lista_arquivos[arquivo]
                }
                resposta = send_to_tracker(dados)
                print(resposta)
                cstracker = resposta["checksum"]
                print(cstracker)
                cs = assemble_file(lista_arquivos[arquivo])
                print(cs)
                if cstracker == cs:
                    print(f"Arquivo reassemblado com sucesso")
                else:
                    raise Exception("Checksum não confere")
            except:
                print("não foi possivel juntar este arquivo por não existir ou nao estar completo")
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "8":
            #8 - Anunciar arquivos manualmente
            print("\n Escolha quais arquivos para anunciar (apenas arquivos.txt são listados)")
            all_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.txt')]

            if not all_files:
                print("Nenhum arquivo .txt encontrado")
                return
            for idx, f in enumerate(all_files):
                print(f"[{idx}] {f}")
            indices = input("Insira os índices seprandos por espaços. Ex: 0 2 3\n").split()
            selected_files = [all_files[int(i)] for i in indices if i.isdigit() and int(i)<len(all_files)]

            print("\n arquivos selecionados:")
            for f in selected_files:
                print(f" - {f}")
                print(f"Selected_files está assim: {selected_files}")
                novos_chunks = announce_file_novo(usuario_logado,f)
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "9":
            #Anunciar todos os chunks
            arquivos = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.txt')]
            print(arquivos)
            try:
                dados = register_chunks(arquivos,usuario_logado)
                dadosarq = register_arquivos(arquivos,usuario_logado)
                resposta = send_to_tracker(dados)
                print(resposta["mensagem"])
                resposta = send_to_tracker(dadosarq)
                print(resposta["mensagem"])
            except:
                print("não foi possivel registrar os chunks")
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "10":
            #Sair do sistema
            dados = {
                "action": "exit",
                "username": usuario_logado
            }
            send_to_tracker(dados)
            usuario_logado = None
            print("sessão finalizada.")
            input("Pressione Enter para continuar.")
            os.system('cls||clear')
            return False
        elif operation == "11":
            # Criar um novo arquivo.txt
            base_name = input("Digite o nome do arquivo a ser criado (sem .txt): ")
            file_name = base_name + ".txt"

            if os.path.exists(file_name):
                print(f"[WARN] O arquivo '{file_name}' já existe.")
                escolha = input("[1] Substituir o arquivo atual\n[2] Digitar outro nome\n[3] Adicionar contador ao nome\n[4] Cancelar\nEscolha: ")

                if escolha == "1":
                    pass  # Segue para sobrescrever
                elif escolha == "2":
                    base_name = input("Digite o novo nome do arquivo (sem .txt): ")
                    file_name = base_name + ".txt"
                elif escolha == "3":
                    contador = 1
                    while True:
                        nome_contador = f"{base_name}_{contador}.txt"
                        if not os.path.exists(nome_contador):
                            file_name = nome_contador
                            break
                        contador += 1
                else:
                    print("[ERRO] Operação cancelada.")
                    continue

            file_size = int(input("Digite o tamanho do arquivo (MB): "))
            create_big_text_file(file_name, file_size)
            print(f"[SUCESSO] Arquivo '{file_name}' criado com sucesso.")

        elif operation == "12":
            #Baixar chunk
            dados = {
                "action": "list_clients",
                "username": usuario_logado
            }
            resposta = send_to_tracker(dados)
            print()
            print("Peers Ativos: ")
            i = 0
            portAssociation = []

            for peer in resposta.get("mensagem", []):
                i += 1
                if(peer == usuario_logado):
                    print(f"[{i}] - {peer} (Você)")
                else:
                    print(f"[{i}] - {peer}")
                    portAssociation.append(peer)
            print(f"PortAssociation: {portAssociation}")
            accept_chat = input(("Gostaria de comunicar com um Peer?\n1-Sim    0-Não\n"))
            if accept_chat == "1":
                #selected_user = input("Digite o nome do usuário que deseja pedir o arquivo\n")
                #Inicialmente, ele apenas escolhe um usuário aleatório, mas depois irá aplicar o incentivo para refazer a escolha
                selected_user = random.choice(portAssociation)
                if selected_user == usuario_logado:
                        print("Não é possível realizar a operação consigo mesmo!")
                else:
                    #Continuação do processo de seleção
                    i = 0
                    for user in resposta.get("mensagem",[]):
                        i += 1                      
                        if selected_user == user or str(i) == selected_user:
                            print("Usuário Escolhido para operação com sucesso!")
                            dados_start_chunk = {
                                "action":"get_peer_info_chunk",
                                "username": user
                            }
                            resposta_start_chunk = send_to_tracker(dados_start_chunk)

                            if resposta_start_chunk.get("status")=="ok":
                                peer_info = resposta_start_chunk.get("mensagem",{})
                                peer_ip = peer_info.get("ip")
                                peer_port = peer_info.get("port")
                                print(f"Iniciando a operação com {user} em {peer_ip}:{peer_port}")

                                print(f"Digite o nome do arquivo para puxar de {user}:")
                                #texto = input("Digite seu arquivo:")
                                caminho = f"arquivos_cadastrados/arquivos_tracker.json"
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
                                            nome_arquivo_sem_extensao = os.path.splitext(nome_escolhido)[0]
                                            print(f"\nVocê escolheu o arquivo: {nome_arquivo_sem_extensao}")
                                            inicio_download = time.time()

                                            dados_chunk_map = {
                                                "action":"get_chunk_owners_online",
                                                "arquivo":nome_arquivo_sem_extensao,
                                                "username":usuario_logado
                                            }
                                            resposta_chunks = send_to_tracker(dados_chunk_map)
                                            print(f"A resposta_chunks é {resposta_chunks}")
                                            if resposta_chunks.get("status") == "ok":
                                                chunk_map = resposta_chunks["chunks"]
                                                volume_total = 0
                                                total_chunks_sum = 0
                                                integridade = True
                                                fila_chunks = queue.Queue()

                                                for chunk_nome, donos in chunk_map.items():
                                                    # Escolhe um peer online (pode usar random ou round-robin futuramente)
                                                    donos_ordenados = sorted(donos,key=lambda peer:get_bytes_score(peer),reverse=True)
                                                    print(f"Ordem de tentativa para {chunk_nome}: {donos_ordenados}")
                                                    fila_chunks.put((chunk_nome, donos_ordenados))
                                                    caminho_chunk = f"chunks_recebidos/{usuario_logado}/{nome_arquivo_sem_extensao}/{chunk_nome}"
                                                    if os.path.exists(caminho_chunk):
                                                        volume_total += os.path.getsize(caminho_chunk)



                                                    chunk_baixado = False
                                                    for peer_dono in donos_ordenados:
                                                        if peer_dono == usuario_logado:
                                                            continue
                                                        dados_peer_info = {
                                                            "action":"get_peer_info_chunk",
                                                            "username":peer_dono
                                                        }
                                                        resposta_info = send_to_tracker(dados_peer_info)

                                                        if resposta_info.get("status") == "ok":
                                                            ip = resposta_info["mensagem"]["ip"]
                                                            port = resposta_info["mensagem"]["port"]

                                                            print(f"Tentando baixar {chunk_nome} de {peer_dono} ({ip}:{port})")
                                                            sucesso = requisitar_chunk(ip,port,usuario_logado,peer_dono,chunk_nome,inicio_download)
                                                            print("o código executou até depois de sucesso")
                                                            registrar_dono_no_json_arquivo(chunk_nome, usuario_logado)
                                                            print(f"O sucesso foi: {sucesso}")
                                                            total_chunks_sum+=1

                                                            if sucesso:
                                                                print(f"O sucesso foi: {sucesso}")
                                                                total_chunks_sum+=2
                                                                chunk_baixado = True
                                                                registrar_dono_no_json_arquivo(chunk_nome, usuario_logado)
                                                                break
                                                        else:
                                                            print(f"Não foi possível obter o IP/porta do {peer_dono}")
                                                    if not chunk_baixado:
                                                        print(f"Falha ao baixar o chunk: {chunk_nome}. Nenhum dos peers respondeu ao pedido")
                                                        integridade = False

                                                print("[SUCESSO] Todos os chunks foram requisitados e baixados.")
                                                adicionar_dono_chunk("arquivos_cadastrados/arquivos_tracker.json", nome_escolhido, usuario_logado)

                                                #Registro Tempo de Download
                                                fim_download = time.time()
                                                tempo_total = fim_download - inicio_download

                                                with open("reports/transfer_report.txt","a",encoding='utf-8') as report_file:
                                                    report_file.write(f" Tempo total de download de TODOS os chunks de {nome_escolhido}: {tempo_total:.2f} segundos.\n")
                                                #registrar_dono_no_json_arquivo(nome_escolhido, usuario_logado)

                                                add_transfer_record(usuario_logado,tempo_total,volume_total,integridade)
                                            else:
                                                    print("[WARN] Não foi possível obter os chunks do arquivo do tracker.")
                                    except ValueError:
                                        print("Entrada inválida. Digite um número.")
                input("Pressione Enter para continuar")
                os.system('cls||clear')
        elif operation == "13":
            #Montar arquivo com base em Chunks
            caminho_pasta = escolher_pasta_para_montar(f"chunks_recebidos/{usuario_logado}")
            if caminho_pasta:
                print(f"Preparando para montar os chunks da pasta: {caminho_pasta}")
                # Aqui você chama a função que monta o arquivo a partir dos chunks nessa pasta
                #
                montar_arquivo(caminho_pasta,usuario_logado)

            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "14":
            menu_index = menu_index + 1
            if menu_index > 2:
                menu_index = 2
        elif operation == "15":
            menu_index = menu_index - 1
            if menu_index <0:
                menu_index = 0
        elif operation == "16":
            # Baixar chunk com múltiplas threads com incentivo

            dados = {
                "action": "list_clients",
                "username": usuario_logado
            }
            resposta = send_to_tracker(dados)
            print("\\nPeers Ativos:")
            portAssociation = [peer for peer in resposta.get("mensagem", []) if peer != usuario_logado]

            for i, peer in enumerate(resposta.get("mensagem", []), start=1):
                status = "(Você)" if peer == usuario_logado else ""
                print(f"[{i}] - {peer} {status}")

            print(f"PortAssociation: {portAssociation}")
            if input("Gostaria de comunicar com um Peer?\\n1-Sim    0-Não\\n") != "1":
                return

            selected_user = random.choice(portAssociation)
            if selected_user == usuario_logado:
                print("Não é possível realizar a operação consigo mesmo!")
                return

            dados_peer = {"action": "get_peer_info_chunk", "username": selected_user}
            resposta_peer = send_to_tracker(dados_peer)
            if resposta_peer.get("status") != "ok":
                return

            print(f"Iniciando operação com {selected_user}")
            caminho = "arquivos_cadastrados/arquivos_tracker.json"
            arquivos, dados = listarArquivos(caminho)

            if not arquivos:
                print("Nenhum arquivo .txt disponível.")
                return

            for i, nome in enumerate(arquivos):
                print(f"[{i}] - {nome}")
            try:
                escolha = int(input("Digite o número do arquivo que deseja selecionar: "))
                if not (0 <= escolha < len(arquivos)):
                    return
                nome_escolhido = arquivos[escolha]
                nome_arquivo_sem_extensao = os.path.splitext(nome_escolhido)[0]
                print(f"Você escolheu: {nome_arquivo_sem_extensao}")
            except ValueError:
                print("Entrada inválida.")
                return

            inicio_download = time.time()
            dados_chunk_map = {
                "action": "get_chunk_owners_online",
                "arquivo": nome_arquivo_sem_extensao,
                "username": usuario_logado
            }
            resposta_chunks = send_to_tracker(dados_chunk_map)
            if resposta_chunks.get("status") != "ok":
                print("[WARN] Não foi possível obter os chunks.")
                return

            chunk_map = resposta_chunks["chunks"]
            volume_total = 0
            fila_chunks = queue.Queue()
            for chunk_nome, donos in chunk_map.items():
                donos_ordenados = sorted(donos, key=lambda peer: get_transmisson_score(peer), reverse=True)
                fila_chunks.put((chunk_nome, donos_ordenados))
                caminho_chunk = f"chunks_recebidos/{usuario_logado}/{nome_arquivo_sem_extensao}/{chunk_nome}"
                if os.path.exists(caminho_chunk):
                    volume_total += os.path.getsize(caminho_chunk)

            def thread_worker(usuario_logado, fila_chunks, inicio_download):
                while not fila_chunks.empty():
                    try:
                        chunk_nome, donos_ordenados = fila_chunks.get_nowait()
                    except queue.Empty:
                        break
                    chunk_sucesso = False
                    for peer_dono in donos_ordenados:
                        if peer_dono == usuario_logado:
                            continue
                        info = get_peer_info(peer_dono)
                        if info:
                            ip = info["ip"]
                            port = info["port"]
                            print(f"Tentando baixar {chunk_nome} de {peer_dono} ({ip}:{port})")
                            sucesso = requisitar_chunk(ip, port, usuario_logado, peer_dono, chunk_nome, inicio_download,False)
                            if sucesso:
                                chunk_sucesso = True
                                print(f"Chunk {chunk_nome} baixado com sucesso.")
                                break
                            if not chunk_sucesso:
                                print(f"[ERRO] Falha ao baixar o chunk {chunk_nome}. Nenhum peer respondeu.")
                                nonlocal integridade
                                integridade = False
                    fila_chunks.task_done()

            todos_donos = [dono for donos in chunk_map.values() for dono in donos if dono != usuario_logado]
            peer_mais_forte = max(todos_donos, key=get_score, default=None)
            score_mais_forte = get_score(peer_mais_forte) if peer_mais_forte else 0
            limite_conexoes = get_limite_conexoes(score_mais_forte)
            print(f"Usando {limite_conexoes} conexões com base no peer {peer_mais_forte} (score: {score_mais_forte})")

            threads = []
            for _ in range(limite_conexoes):
                t = threading.Thread(target=thread_worker, args=(usuario_logado, fila_chunks, inicio_download))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

            if integridade:
                adicionar_dono_chunk("arquivos_cadastrados/arquivos_tracker.json", nome_escolhido, usuario_logado)
                print("[SUCESSO] Todos os chunks foram baixados com sucesso e integridade verificada.")
            else:
                print("[WARN] Não foi possível obter todos os chunks. O arquivo não será registrado como completo.")
            fim_download = time.time()
            tempo_total = fim_download - inicio_download
            with open("reports/transfer_report.txt", "a", encoding='utf-8') as report_file:
                report_file.write(f" Tempo total de download de TODOS os chunks de {nome_escolhido}: {tempo_total:.2f} segundos.\\n")

            add_transfer_record_Connections(usuario_logado, tempo_total, volume_total, True)
            input("Pressione Enter para continuar")
            os.system('cls||clear')

        elif operation == "17":
            plotarGraficoSingle()
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "18":
            plotarGraficoMultiplas()
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "1":
            pedido = {"action" : "list_files",  "username": usuario_logado}
            resposta = send_to_tracker(pedido)
            #arquivos_desejados(resposta) # O cliente pode escolher qual arquivo ele quer baixar
            verificar_chunks_faltantes(username=usuario_logado, nome_arquivo="Asdf")
            input("Pressione Enter para continuar")
            os.system('cls||clear')




        else:
            print("Opção inválida.")
            input("Pressione Enter para continuar")
            os.system('cls||clear')


def init():
    while True:
        print('Bem vindo ao WhatsApp#2!')
        print('Gostaria de Iniciar o Tracker?\n 1- Sim, 0 - Não')

        ans = int(input())
        if ans == 1:
            if is_tracker_running():
                print("Tracker já está rodando.")
            else:
                print("Não está rodando ainda")
                launch_tracker_cross_platform()
                print("Tracker Inicializado!")

            print("=====BEM VINDO======\nAO WHATSAPP#2")
            result = interactiveMenu_1()
            if result:
                print("Continue!")
                a = int(input())
            else:
                print("End of Program")
                break
        else:
            os.system('cls||clear')
            print("Gostaria de se comportar como um cliente?\n")
            ans2 = int(input(" 1- Sim, 0 - Não\n"))
            if (ans2==1):
                #print("Implementar verificação de existência de Tracker Aitvo!")
                print("=====BEM VINDO======\nAO WHATSAPP#2")
                result = interactiveMenu_1()
                if(result):
                    print("Continue!")
                    a = int(input())
                else:
                    print("End of Program")
                    break
            os.system('cls||clear')

if __name__ == "__main__":
    init()