import socket
import threading
import json
from datetime import datetime
import os
from chunks_modules import *
from scoring import *
import time
import random
from peer import calculate_checksum
import sys
from typing import List

ARQUIVO_JSON = "chunks_trocados.json"

def mostrar_progresso(recebidos, total):
    """Exibe uma barra de progresso simples no terminal."""
    largura = 30
    preenchidos = int((recebidos / total) * largura)
    barra = '█' * preenchidos + '-' * (largura - preenchidos)
    percentual = (recebidos / total) * 100
    sys.stdout.write(f'\r[{barra}] {percentual:.1f}% ({recebidos}/{total} bytes)')
    sys.stdout.flush()

def start_peer_server(chat_port,chunk_port, meu_username) -> None:
    """
    Inicia o servidor de um peer para receber mensagens diretas de outros peers.

    - Escuta na porta especificada por `chat_port`.
    - Para cada conexão recebida, uma nova thread é criada para tratar a mensagem.
    - Exibe no terminal a mensagem recebida, junto do remetente e timestamp.

    Args:
        chat_port (int): Porta local na qual o peer escutará mensagens.
        meu_username (str): Nome de usuário do peer atual (não usado diretamente aqui,
                            mas pode ser útil para logs ou verificações futuras).
    """
    def carregar_peers_com_chunks(meu_username):
        """
        Retorna a lista de nomes dos chunks que o peer realmente possui,
        vasculhando a pasta de chunks do usuário.
        """
        base_path = f"arquivos_cadastrados/chunkscriados/{meu_username}"
        chunks_possuídos = []

        if not os.path.exists(base_path):
            print("[ERRO] Nenhum diretório de chunks encontrado para o usuário.")
            return []

        for nome_arquivo in os.listdir(base_path):
            caminho_subpasta = os.path.join(base_path, nome_arquivo)
            if not os.path.isdir(caminho_subpasta):
                continue

            for nome_json in os.listdir(caminho_subpasta):
                if nome_json.endswith(".json"):
                    caminho_json = os.path.join(caminho_subpasta, nome_json)
                    try:
                        with open(caminho_json, 'r', encoding='utf-8') as f:
                            chunks_info = json.load(f)
                            for chunk in chunks_info:
                                chunk_nome = chunk.get("nome")
                                if chunk_nome:
                                    chunks_possuídos.append(chunk_nome)
                    except Exception as e:
                        print(f"[ERRO] Erro ao ler {caminho_json}: {e}")

        print(f"[CHEGOU] Chunks efetivamente presentes com {meu_username}: {chunks_possuídos}")
        return chunks_possuídos

    def handle_connection(conn):
        try:
            buffer = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buffer += chunk

            mensagem = json.loads(buffer.decode())
            if mensagem['timestamp']:
                print(f"\n[RECEBIDO] Nova mensagem de {mensagem['from']}:")
                print(f"[MENSAGEM]   {mensagem['message']} ({mensagem['timestamp']})\n")
        except Exception as e:
            print(f"[ERRO] Erro ao receber mensagem: {e}")
            
        finally:
            conn.close()
    def server_loop(chat_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', chat_port))
        s.listen()
        print(f"[Servidor Chunks] Aguardando requisições de chunks em localhost:{chat_port}...\n")

        while True:
            print(chat_port)
            conn, addr = s.accept()
            threading.Thread(target=handle_connection, args=(conn,), daemon=True).start() 
    def chunk_server_loop(chunk_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', chunk_port))
        s.listen()
        print(f"[Servidor Chunks] Aguardando requisições de chunks em localhost:{chunk_port}...\n")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_chunk_request, args=(conn,), daemon=True).start()
    def handle_chunk_request(conn):
        def salvar_transmissao(peer_user, nome_chunk, tamanho, tempo):
            registro = {
                "peer_user": peer_user,
                "chunk": nome_chunk,
                "tamanho": tamanho,
                "tempo": tempo
            }
            arquivo = "reports/transmissions.json"
            registros = []
            if os.path.exists(arquivo):
                with open(arquivo, "r") as f:
                    registros = json.load(f)
            registros.append(registro)
            with open(arquivo, "w") as f:
                json.dump(registros, f, indent=4)
            peer_user = None
        try:
            print("Request chegou!", flush=True)
            requisicao = conn.recv(1024).decode()
            requisicao_json = json.loads(requisicao)
            nome_chunk = requisicao_json.get("nome_chunk")
            user_to = requisicao_json.get("to")
            user_from = requisicao_json.get("from")

            #Salva o nome do peer para atualização depois
            peer_user = user_from
            print(f"[INFO] nome_chunk: {nome_chunk}\nuser_to: {user_to}\nuser_from: {user_from} \npeer_user: {peer_user}")

            #Marca conexão ativa (+1)
            update_score(peer_user,0,0,0,active_connections=1)
            #input(f"[DEBUG] Verifique o JSON após AUMENTAR active_connections para {peer_user}. Pressione Enter para continuar...")
            

            # [SUCESSO] Recarrega a cada request:
            print(f"[INFO] The score was updated!")
            caminho_json_chunks = "arquivos_cadastrados/arquivos_tracker.json"
            chunks_disponiveis = carregar_peers_com_chunks(meu_username)
            print("[INFO] We found out the avaiable chunks!")
            #NOVO - Verificamos se existe umdiretório de chunks recebidos
            caminho_arquivo = nome_chunk.split('.')[0]
            caminho_recebidos = f"chunks_recebidos/{meu_username}/{caminho_arquivo}/{nome_chunk}"
            tem_chunk_recebido = os.path.exists(caminho_recebidos)

            print(f"[INFO] Chunks disponiveis para {meu_username} transmitir são: {chunks_disponiveis}")
            print(f"[INFO] Existe no diretório de recebidos?: {'SIM' if tem_chunk_recebido else 'NÃO'}")



            print("O JSON DE REQUISIÇÃO É: ")
            print(requisicao_json, flush=True)
            print(f"from user: {user_from}\n to_user: {user_to}\n nome_chunk:{nome_chunk}")


            print(f"Chunks disponiveis para transmitir são: {chunks_disponiveis}")
            print(f"Existe no diretório de recebidos?: {'SIM' if tem_chunk_recebido else 'NÃO'}")

            # Verifica se o chunk está registrado NO JSON ou existe NO RECEBIDO
            if nome_chunk in chunks_disponiveis or tem_chunk_recebido:
                # Se existe no diretório de recebidos, atualiza o caminho para enviar
                if tem_chunk_recebido:
                    caminho = caminho_recebidos
                else:
                    caminho = f"arquivos_cadastrados/chunkscriados/{user_to}/{caminho_arquivo}/{nome_chunk}"
                    print(f"[INFO] O caminho na busca é: {caminho}")
                if os.path.exists(caminho):
                    # Calcula o checksum corretamente
                    with open(caminho, 'rb') as f:
                        dados_chunk = f.read()
                    checksum = hashlib.sha256(dados_chunk).hexdigest()

                    print(f"[INFO] O nome do chunk é {nome_chunk}\n o checksum é {checksum}")

                    # Prepara JSON com nome e checksum
                    json_data = [{
                        "nome": nome_chunk,
                        "checksum": checksum
                    }]
                    print("JSON de peer foi gerado! Agora só falta enviar")
                    json_str = json.dumps(json_data)
                    json_bytes = json_str.encode()

                    # Envia o tamanho e o JSON
                    conn.send(len(json_bytes).to_bytes(4, byteorder='big'))
                    conn.send(json_bytes)
                    score_peer = get_score(peer_user)
                    bandwidth_limit = calcular_bandwidth(score_peer)

                    min_chunk_size = 100 * 1024# Min Chunk_size = 100 KB
                    max_chunk_size = 2* 1024 * 1024 #Max chunk size = 2MB

                    MAX_BANDWIDTH = 10 * 1024 * 1024
                    prop = min(bandwidth_limit / MAX_BANDWIDTH, 1.0)

                    chunk_size = int(min_chunk_size + prop * (max_chunk_size - min_chunk_size))
                    sleep_interval  = (chunk_size / bandwidth_limit)
                    sleep_interval = max(0.5, min(sleep_interval, 1.5))
                    print(f"It sleeps for: {sleep_interval} seconds")
                    print(f"[✓] Peer '{peer_user}' com score {score_peer} vai usar chunk_size {chunk_size} e banda de {bandwidth_limit} B/s")
                    bytes_enviados = 0
                    inicio = time.time()

                    while bytes_enviados < len(dados_chunk):
                        if conn.fileno() == -1:
                            break
                        parte = dados_chunk[bytes_enviados:bytes_enviados+chunk_size]
                        print(f"[INFO] Parte é: {parte}\n Enviando chunk a partir do offset: {bytes_enviados}\nlen_dados_chunk: {len(dados_chunk)}")
                        conn.sendall(parte)
                        bytes_enviados += len(parte)
                        porcentagem = (bytes_enviados / len(dados_chunk)) * 100
                        print(f"[INFO] Bytes enviados atualizados: {bytes_enviados}/{len(dados_chunk)} ({porcentagem:.2f}%)")

                        tempo_estimado = len(parte) / bandwidth_limit
                        time.sleep(min(max(tempo_estimado,0.05),1.5))
                        #print(f"It's sleeping for {sleep_interval:.2f} seconds...")
                        time.sleep(sleep_interval)
                        #print(f"It's sleeping for {sleep_interval}")
                        #time.sleep(sleep_interval)
                        #print("It has just slept")
                    #fim = time.time()
                    #tempo_transferencia = fim - inicio
                    fim = time.time()
                    tempo_total = fim - inicio
                    update_score(peer_user,
                            bytes_sent=len(dados_chunk),
                            successful_responses=1)
                    print(f"[✓] Chunk '{nome_chunk}' enviado com throttling ({chunk_size} bytes por pacote, {bandwidth_limit} bytes/s).")
                    salvar_transmissao(peer_user, nome_chunk, len(dados_chunk), time.time() - inicio)

                    # Envia o chunk
                    #conn.sendall(dados_chunk)

                    print(f"[✓] Chunk '{nome_chunk}' enviado com sucesso.")

                else:
                    # Caso de erro:
                    if not os.path.exists(caminho):
                        conn.send(b"ERRO: Chunk nao encontrado.")
                        conn.shutdown(socket.SHUT_WR)
                        #update_score(peer_user,
                        #            failed_transfers=1,
                        #            integrity_check=False)
            else:
                conn.send(b"ERRO: Chunk nao disponivel.")
                conn.shutdown(socket.SHUT_WR)
                #update_score(peer_user,
                #    failed_transfers=1,
                #    integrity_check=False)

        except Exception as e:
            #print(f"[Erro Chunk] {e}")
            return
        finally:
            #  Marca o final da conexão (-1) para o peer
            if peer_user:
                update_score(peer_user, 0, 0, 0, active_connections=-1)
            conn.close()
    threading.Thread(target=server_loop, args=(chat_port,), daemon=True).start()
    threading.Thread(target=chunk_server_loop, args=(chunk_port,), daemon=True).start()
    threading.Thread(target=p2p, args=(meu_username,), daemon=True).start()
    
def calcular_bandwidth(score_peer, min_rate=10*1024, max_rate=3*1024*1024, max_score=100000):
    """
    Converte o score do peer numa largura de banda (bytes/s) com escala logarítmica.
    """
    print(f"[INFO] The peer's score is {score_peer}")
    score_peer = max(score_peer, 1)  # evita log(0)
    escala = math.log(score_peer + 1) / math.log(max_score + 1)
    bandwidth = min_rate + (max_rate - min_rate) * escala
    print(f"[INFO] log escala: {escala:.4f} -> bandwidth: {bandwidth:.2f} bytes/s")
    return int(bandwidth)

def send_to_tracker2(data) -> dict:
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

def p2p(user):
    def timeconected():
        dados_start_chat = {
        "action":"get_ip",
        "username": user
        }
        while True:
            time.sleep(1)
            resposta = send_to_tracker2(dados_start_chat)
            peers_ip = resposta["mensagem"]             # Pega os ips, ports e usarios correspondentes
            for peer_user, ip, port in peers_ip:
                update_score(peer_user, 0, 1)
                #print(f"[INFO] Score atualizado para {peer_user}. Verifique o arquivo JSON.")
    threading.Thread(target=timeconected, daemon=True).start()
    while True:
        score = get_score(user)
        if score <= 30:
            for i in range(1):
                threading.Thread(target=pedir_chunks, args=(user,), daemon=True).start()
        elif score < 80:
            for i in range(4):
                threading.Thread(target=pedir_chunks, args=(user,), daemon=True).start()
        else:
            for i in range(8):
                threading.Thread(target=pedir_chunks, args=(user,), daemon=True).start()

        time.sleep(1)

def pedir_chunks(user):
    getip = {
        "action":"get_ip",
        "username": user
    }
    getfile = {
        "action":"list_files",
        "username": user
    }
    global arquivosdesejados
    resposta = send_to_tracker2(getip)# Pega todos os ips (Sempre renovando)
    peers_ip = resposta["mensagem"]             # Pega os ips, ports e usarios correspondentes
    resposta = send_to_tracker2(getfile)
    files_peer = resposta["mensagem"]
    for file in arquivosdesejados:
        #print(f"\n🔎 Procurando peers com o arquivo: {file}")
        # Verifica quem tem esse arquivo entre os peers listados em files_peer
        for peer_id, arquivos_que_tem in files_peer.items():
            if file in arquivos_que_tem and peer_id != user:
                
                # Descobre IP e porta do peer atual
                peer_info = next((p for p in peers_ip if p[0] == peer_id), None)
                #print(peer_info)
                if peer_info is None:
                    continue  # IP e porta não encontrados no peers_ip
                users, ip, port = peer_info
                
                for users, ip, port in peers_ip:            # envia para todos os peers
                    if users != user:
                        #print(f"The users is {users} and the user is: {user}")
                        #print("Therefore we're both different from each other!")
                        nome_do_chunk, dados = escolher_chunk_compatível(user)

                        if nome_do_chunk is None:
                            #print(f"[{user}] Nenhum chunk compatível encontrado no momento.")
                            continue  # ou `break`, dependendo da lógica desejada

                        basename_chunk = os.path.basename(nome_do_chunk)
                        if basename_chunk:                   # Se eu for capaz de enviar
                            try: 
                                #print(f"[{user}] Enviando o pedido do chunk {os.path.basename(basename_chunk)} para {ip} : {port}")
                                enviado = send_chunk(user,users, ip, port, basename_chunk, dados)# Vai enviar para esse ip pedindo um chunk aleatorio que eu preciso
                                if enviado:                     # Se foi enviado o pedido com sucesso
                                    successful_responses = 1
                                    bytes_sent = 1
                                    update_score(user, bytes_sent, 0, successful_responses)
                                    #print(user,"enviando para", users)
                                else:
                                    bytes_sent = -5
                                    #print("nao deu kk")
                                    #update_score(user, 0, 0, 0, failed_transfers=1)
                            except Exception as e:
                                #rint(f"Não foi possível enviar o pedido para o peer {users}: {e}")
                                return
                        else:                               # mesmo qie nao tenha conseguido enviar vamos dar um incentivo a ele
                            break

def send_chunk(user,users, ip, port, nome_chunk, dados):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        # Envia a requisição de chunk como JSON
        mensagem = {"enviando": nome_chunk,
                   #"dados"   :  dados,
                   "sender"    : user,
                   "to": users,
                   "from": user,
                   "nome_chunk": nome_chunk
                   }
        enviado = json.dumps(mensagem)
        s.sendall(enviado.encode())
        s.shutdown(socket.SHUT_WR)
        #print(f"[✓] Chunk '{nome_chunk}' enviado com sucesso")
        # Recebe os dados do chunk
        buffer = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buffer += chunk
        #print(buffer)
        resposta_raw = buffer.decode().strip()

        if resposta_raw.startswith("ERRO"):
            print(f"[Erro recebido do servidor]: {resposta_raw}")
            return False

        mensagem = json.loads(resposta_raw)

        #Primeiro ler os 4 bytes que indicam o tamanho do JSON
        tamanho_json = int.from_bytes(s.recv(4),byteorder='big')
        json_bytes = b''
        while len(json_bytes) < tamanho_json:
            parte = s.recv(tamanho_json - len(json_bytes))
            if not parte:
                break
            json_bytes += parte
        json_data = json.loads(json_bytes.decode())
        # atualiza a pontuação daquele peer:
        #new_score = update_score(peer_id, bytes_sent=0,
        #                 time_connected=ttf,
        #                 successful_responses=successful)
        print("JSON recebido decodificado:", json_bytes.decode())

        s.close()
        return True
    except Exception as e:
        #print(f"[Erro ao enviar pedir pedaços] {e}")
        return False


#CHUNKS_FOLDER = "arquivos_cadastrados/chunkscriados/bigfile/"
CHUNKS_CRIADOS_BASE = "arquivos_cadastrados/chunkscriados"
CHUNKS_RECEBIDOS_BASE = "arquivos_cadastrados/chunks_recebidos"


def escolher_chunk_compatível(usuario):
    """
    Seleciona aleatoriamente um chunk (arquivo .part) entre os que o usuário possui.
    Pode ser tanto da pasta de chunks criados quanto da de recebidos.
    """
    todosChunks = []

    # Verifica em ambas as pastas
    for base_path in [CHUNKS_CRIADOS_BASE, CHUNKS_RECEBIDOS_BASE]:
        pasta_usuario = os.path.join(base_path, usuario)
        if not os.path.exists(pasta_usuario):
            continue

        for subpasta in os.listdir(pasta_usuario):
            caminho_subpasta = os.path.join(pasta_usuario, subpasta)
            if os.path.isdir(caminho_subpasta):
                for arquivo in os.listdir(caminho_subpasta):
                    if arquivo.startswith(subpasta) and ".part" in arquivo:
                        todosChunks.append(os.path.join(caminho_subpasta, arquivo))

    if not todosChunks:
        return None, None

    random.shuffle(todosChunks)
    caminho_chunk = todosChunks[0]
    with open(caminho_chunk, "r", encoding="utf-8") as arquivo:
        dados = arquivo.read()

    return caminho_chunk, dados

def send_chunk_to_peer(ip, port, nome_chunk, destino_arquivo):
    """
    Solicita um chunk a um peer remoto e salva o conteúdo em um arquivo local.

    Args:
        ip (str): IP do peer que possui o chunk.
        port (int): Porta de chunks do peer remoto.
        nome_chunk (str): Nome do chunk que será solicitado.
        destino_arquivo (str): Caminho do arquivo onde o chunk será salvo localmente.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))

        # Envia a requisição de chunk como JSON
        requisicao = json.dumps({"chunk": nome_chunk})
        s.sendall(requisicao.encode())
        s.shutdown(socket.SHUT_WR)

        # Recebe os dados do chunk
        with open(destino_arquivo, 'wb') as f:
            while True:
                dados = s.recv(4096)
                if not dados:
                    break
                f.write(dados)

        print(f"[✓] Chunk '{nome_chunk}' recebido e salvo como '{destino_arquivo}'.")
        s.close()

    except Exception as e:
        print(f"[Erro ao solicitar chunk] {e}")

def send_message_to_peer(ip, port, from_user, to_user, text) -> None:
    """
    Envia uma mensagem para um peer específico via conexão TCP.

    Args:
        ip (str): Endereço IP do peer destinatário.
        port (int): Porta TCP do peer destinatário.
        from_user (str): Nome do usuário remetente.
        to_user (str): Nome do usuário destinatário.
        text (str): Conteúdo da mensagem a ser enviada.

    O formato da mensagem enviada é um JSON contendo remetente, destinatário,
    texto da mensagem e timestamp do envio.
    """
    mensagem_json = {
        "from": from_user,
        "to": to_user,
        "message": text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.sendall(json.dumps(mensagem_json).encode())
        s.shutdown(socket.SHUT_WR)
        s.close()
        print(f"\n Mensagem enviada para {to_user} ({ip}:{port})[SUCESSO]\n")
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

def announce_files (username) -> None:
    """
    Permite ao usuário selecionar arquivos .txt locais para anunciar ao tracker.

    - Lista todos os arquivos .txt no diretório atual.
    - Solicita ao usuário que escolha quais arquivos deseja anunciar, indicando índices.
    - Envia a lista selecionada ao tracker na ação "update_files".
    - Recebe e exibe a resposta do servidor.

    Args:
        username (str): Nome de usuário que está anunciando os arquivos.
    """
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
    dados = {
        "action": "update_files",
        "username": username,
        "files": selected_files
    }
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 5000))
        s.sendall(json.dumps(dados).encode())
        s.shutdown(socket.SHUT_WR)

        buffer = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buffer += chunk
        resposta = json.loads(buffer.decode())
        print("\n=> Resultado do anúncio:", resposta.get("mensagem"))
    except Exception as e:
        print("[ERRO] Erro ao anunciar arquivos:", e)

def construir_tamanhos_chunks_fixos(nome_arquivo: str, tamanho_max_chunk_bytes: int = 2 * 1024 * 1024) -> List[int]:
    """
    Gera uma lista de tamanhos (em bytes) para dividir um arquivo em chunks de tamanho fixo máximo,
    onde o último chunk pode ser menor.

    Parâmetros:
        nome_arquivo (str): Caminho do arquivo.
        tamanho_max_chunk_bytes (int): Tamanho máximo de cada chunk em bytes.

    Retorna:
        List[int]: Lista de tamanhos dos chunks em bytes.
    """
    tamanho_arquivo_bytes = os.path.getsize(nome_arquivo)
    num_chunks = (tamanho_arquivo_bytes + tamanho_max_chunk_bytes - 1) // tamanho_max_chunk_bytes  # teto da divisão

    tamanho_chunk = tamanho_arquivo_bytes // num_chunks
    tamanhos_chunks = [tamanho_chunk] * (num_chunks - 1)

    ultimo_chunk = tamanho_arquivo_bytes - tamanho_chunk * (num_chunks - 1)
    tamanhos_chunks.append(ultimo_chunk)

    return tamanhos_chunks

def construir_tamanhos_chunks_aleatorios(nome_arquivo, min_chunks=2, max_chunks=50, min_chunk_size=100*1024):
    """
    Gera uma lista de tamanhos (em bytes) para dividir um arquivo em chunks aleatórios,
    garantindo:
    - Número de chunks entre min_chunks e max_chunks.
    - Tamanho mínimo por chunk definido por min_chunk_size.
    - A soma total dos chunks igual ao tamanho do arquivo.

    Parâmetros:
        nome_arquivo (str): Caminho do arquivo.
        min_chunks (int): Número mínimo de chunks.
        max_chunks (int): Número máximo de chunks.
        min_chunk_size (int): Tamanho mínimo para cada chunk em bytes.

    Retorna:
        List[int]: Lista de tamanhos dos chunks em bytes.
    """
    tamanho_total = os.path.getsize(nome_arquivo)

    # Limite superior de chunks não pode ser maior que o número de bytes
    max_chunks = min(max_chunks, tamanho_total)

    # Garante que min_chunks nunca ultrapasse max_chunks
    if min_chunks > max_chunks:
        min_chunks = max_chunks

    num_chunks = random.randint(min_chunks, max_chunks)

    tamanhos = []
    base_size = tamanho_total // num_chunks
    resto = tamanho_total % num_chunks

    for i in range(num_chunks):
        tamanho_chunk = base_size + (1 if i < resto else 0)
        tamanhos.append(tamanho_chunk)

    return tamanhos

def announce_file_novo(username, nome_arquivo):
    """
    Divide um arquivo em chunks, calcula seu checksum e o anuncia para o tracker via socket TCP.

    Parâmetros:
        username (str): Nome do usuário que está anunciando o arquivo.
        nome_arquivo (str): Caminho do arquivo a ser dividido e anunciado.
    """
    #Divisão do arquivo em chunks de tamanhos aleatórios
    print(f"O nome_arquivo é: {nome_arquivo}")
    tamanho_arquivo_bytes = os.path.getsize(nome_arquivo)
    print(tamanho_arquivo_bytes)
    #tamanho_arquivo_mb = tamanho_arquivo_bytes / (1024 * 1024)
    tamanhos_chunks = construir_tamanhos_chunks_aleatorios(nome_arquivo)

    print(f"Os tamanhos aleatórios são {tamanhos_chunks}")

    chunks_info = dividir_em_chunks_user(nome_arquivo, tamanhos_chunks,username)

    print(f"chunks_info é:")
    if not chunks_info:
        print("[ERRO] Erro ao dividir o arquivo.")
        return
    
    #Calculo do checksum
    with open(nome_arquivo, 'rb') as f:
        conteudo = f.read()
        checksum = hashlib.sha256(conteudo).hexdigest()

    print("O arquivo foi divido em chunks!")
    nome_pasta = os.path.splitext(nome_arquivo)[0]
    print(f"[INFO] O nome_pasta é:{nome_pasta}")
    caminho_chunks = f"arquivos_cadastrados/chunkscriados/{username}/{nome_pasta}"
    json_path = caminho_chunks+"/"+nome_pasta+".json"
    #json_path = os.path.join(caminho_chunks, nome_pasta + ".json")


    with open(json_path, 'r') as jf:
        chunks_info = json.load(jf)
    #print(f"O conteúdo de chunks_info é: {chunks_info}")

    nomes_chunks = [chunk['nome'] for chunk in chunks_info]
    print(nomes_chunks)

    dados = {
        "action": "announce_file",
        "username": username,
        "arquivo": {
            "nome": nome_arquivo,
            "checksum": checksum,
            "chunks_path": caminho_chunks,
            "chunks": nomes_chunks
        }
    }

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 5000))
        s.sendall(json.dumps(dados).encode())
        s.shutdown(socket.SHUT_WR)

        buffer = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buffer += chunk

        resposta = json.loads(buffer.decode())
        print("\n=> Resultado do anúncio:", resposta.get("mensagem"))
        return nomes_chunks

    except Exception as e:
        print("[ERRO] Erro ao anunciar arquivo:", e)

arquivosdesejados = ['Asdf.txt'] # o peer pode escolher qual arquivo ele quer baixar

def arquivos_desejados(resposta):
    global arquivosdesejados
    arquivosdesejados = []

    # Extrai todos os arquivos únicos da mensagem
    arquivos_por_peer = resposta["mensagem"]
    todos_arquivos = set()
    for arquivos in arquivos_por_peer.values():
        todos_arquivos.update(arquivos)
    lista_arquivos = sorted(todos_arquivos)

    # Exibe lista com índice
    print(f"\nArquivos disponíveis para escolher:")
    print(f"[0] - Todos os arquivos")
    for i, nome in enumerate(lista_arquivos, 1):
        print(f"[{i}] - {nome}")

    # Escolha do usuário
    while True:
        try:
            escolha = int(input("\n📥 Digite o número do arquivo que deseja baixar: "))
            if 1 <= escolha <= len(lista_arquivos):
                arquivo_escolhido = lista_arquivos[escolha - 1]
                print(f"\n[SUCESSO] Você escolheu: {arquivo_escolhido}\n")
                arquivosdesejados.append(arquivo_escolhido)
                break
            elif escolha == 0:
                arquivosdesejados.extend(lista_arquivos)
                print("\n[SUCESSO] Você escolheu TODOS os arquivos!")
                for a in lista_arquivos:
                    print(f"  - {a}")
                break
            else:
                print("[ERRO] Número inválido. Tente novamente.")
        except ValueError:
            print("[ERRO] Entrada inválida. Digite apenas o número.")
