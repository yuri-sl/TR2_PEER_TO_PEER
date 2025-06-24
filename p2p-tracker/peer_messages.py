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
    def carregar_peers_com_chunks(caminho_json, meu_username):
        if not os.path.exists(caminho_json):
            print("NÃO EXISTEM ARQUIVOS COM O MEU PEER!")
            return []

        with open(caminho_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            print("DADOS CARREGADOS DO JSON")

        chunks_do_usuario = []
        for info_arquivo in dados.values():
            donos = info_arquivo.get('donos', [])
            if meu_username in donos:
                chunks = info_arquivo.get('chunks', [])
                chunks_do_usuario.extend(chunks)
        print(f"OS CHUNKS REGISTRADOS EM MEU USER SÃO:{chunks_do_usuario}")
        return chunks_do_usuario
    def handle_connection(conn, addr):
        try:
            buffer = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buffer += chunk

            mensagem = json.loads(buffer.decode())
            try:
                print(f"\n📩 Nova mensagem de {mensagem['from']}:")
                print(f"   {mensagem['message']} ({mensagem['timestamp']})\n")
            except:
                #print(f"chunk recebido {mensagem['enviando']}:")
                ARQUIVO_JSON = "chunks_trocados.json"
                sender = mensagem["sender"]
                nome_arquivo = mensagem["enviando"]
                dados = mensagem["dados"].encode()

                # Tenta carregar o JSON existente
                if os.path.exists(ARQUIVO_JSON):
                    with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                        try:
                            dados_existentes = json.load(f)
                        except json.JSONDecodeError:
                            dados_existentes = {}
                else:
                    dados_existentes = {}

                # Se o sender ainda não tem nada salvo, cria entrada vazia
                if sender not in dados_existentes:
                    dados_existentes[sender] = {}

                # Adiciona ou atualiza o arquivo recebido do sender
                checksum = calculate_checksum(dados)
                dados_existentes[sender][nome_arquivo] = checksum

                # Salva de volta no JSON
                with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
                    json.dump(dados_existentes, f, indent=4, ensure_ascii=False)

                #print(f"[✓] Chunk '{mensagem['enviando']}' salvo/atualizado em '{ARQUIVO_JSON}'")
        except Exception as e:
            print(f"Erro ao receber mensagem: {e}")
            
        finally:
            conn.close()

    def server_loop():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', chat_port))
        s.listen()
        print(f"[Servidor] Aguardando mensagens em localhost:{chat_port}...\n")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_connection, args=(conn, addr), daemon=True).start()
    def chunk_server_loop():
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
            user_to = requisicao_json["to"]
            user_from = requisicao_json["from"]

            #Salva o nome do peer para atualização depois
            peer_user = user_from

            #Marca conexão ativa (+1)
            update_score(peer_user,0,0,0,active_connections=1)
            #input(f"[DEBUG] Verifique o JSON após AUMENTAR active_connections para {peer_user}. Pressione Enter para continuar...")
            

            # ✅ Recarrega a cada request:
            caminho_json_chunks = "arquivos_cadastrados/arquivos_tracker.json"
            chunks_disponiveis = carregar_peers_com_chunks(caminho_json_chunks, meu_username)

            #NOVO - Verificamos se existe umdiretório de chunks recebidos
            caminho_arquivo = nome_chunk.split('.')[0]
            caminho_recebidos = f"chunks_recebidos/{meu_username}/{caminho_arquivo}/{nome_chunk}"
            tem_chunk_recebido = os.path.exists(caminho_recebidos)

            print(f"Chunks disponiveis para {meu_username} transmitir são: {chunks_disponiveis}")
            print(f"Existe no diretório de recebidos?: {'SIM' if tem_chunk_recebido else "NÃO"}")



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
                    print(f"O caminho na busca é: {caminho}")
                if os.path.exists(caminho):
                    # Calcula o checksum corretamente
                    with open(caminho, 'rb') as f:
                        dados_chunk = f.read()
                    checksum = hashlib.sha256(dados_chunk).hexdigest()

                    print(f"O nome do chunk é {nome_chunk}\n o checksum é {checksum}")

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

                    chunk_size = min(128 * 1024, len(dados_chunk))
                    sleep_interval = sleep_interval = min(chunk_size / bandwidth_limit, 1.0)
                    print(f"It sleeps for: {sleep_interval} seconds")
                    bytes_enviados = 0
                    inicio = time.time()

                    while bytes_enviados < len(dados_chunk):
                        if conn.fileno() == -1:
                            break
                        parte = dados_chunk[bytes_enviados:bytes_enviados+chunk_size]
                        print(f"Parte é: {parte}\nbytes_enviados: {bytes_enviados}\nlen_dados_chunk: {len(dados_chunk)}")
                        conn.sendall(parte)
                        bytes_enviados += len(parte)
                        print(f"It's sleeping for {sleep_interval}")
                        time.sleep(sleep_interval)
                        print("It has just slept")
                    fim = time.time()
                    #tempo_transferencia = fim - inicio
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
                        update_score(peer_user,
                                    failed_transfers=1,
                                    integrity_check=False)
            else:
                conn.send(b"ERRO: Chunk nao disponivel.")
                update_score(peer_user,
                    failed_transfers=1,
                    integrity_check=False)

        except Exception as e:
            print(f"[Erro Chunk] {e}")
        finally:
            #  Marca o final da conexão (-1) para o peer
            if peer_user:
                update_score(peer_user, 0, 0, 0, active_connections=-1)
                #input(f"[DEBUG] Verifique o JSON após REDUZIR active_connections para {peer_user}. Pressione Enter para continuar...")
            conn.close()
    #Inicia o servidor de chat
    threading.Thread(target=server_loop, daemon=True).start()
    threading.Thread(target=chunk_server_loop, daemon=True).start()
    #print(f"Chunks disponíveis carregados para {meu_username}: {chunks_disponiveis}")
    #if chunks_disponiveis:
    #    threading.Thread(target=chunk_server_loop, daemon=True).start()
    #    print("Os seus chunks foram carregados com sucesso!")
    load_scoreboard()
    threading.Thread(target=p2p, args=(meu_username,), daemon=True).start()
    
def calcular_bandwidth(score_peer, min_rate=10240 , max_rate=1024*1024, max_score=1000000):
    """
    Converte o score do peer numa largura de banda (bytes/s).
    10240 = 10 KB/s
    1024*1024 = 1 MiB/s
    """
    print(f"The peer's score is {score_peer}")
    normalized = min(score_peer / max_score, 1.0)  # Normaliza para 0–1
    bandwidth = min_rate + (max_rate - min_rate) * normalized
    print(f"normalized: {normalized}\n bandwidth: {bandwidth}")
    return int(bandwidth)

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
                update_score(peer_user, 0, 1, 0)
                #print(f"[INFO] Score atualizado para {peer_user}. Verifique o arquivo JSON.")
    threading.Thread(target=timeconected, daemon=True).start()

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
    dados_start_chat = {
        "action":"get_ip",
        "username": user
    }
    time_connected = 0
    update_score(user,0, 0, 0)
    while True:
        #print(bytes_sent)
        time.sleep(1)                                # A cada 1 segundo manda chunk pra todo mundo
        successful_responses = 0
        bytes_sent = 0

        resposta = send_to_tracker2(dados_start_chat)# Pega todos os ips (Sempre renovando)
        peers_ip = resposta["mensagem"]             # Pega os ips, ports e usarios correspondentes
        peers = []
        peers_incentivo = []
        for u, ip, port in peers_ip:                # Coloco os scores junto as infos
            if u != user:
                score_do_peer = get_score(u)
                peers.append((u, ip, port, score_do_peer))
        try:    # tenta calcular o teto 
            teto = max(1, max(peer[3] for peer in peers))       # Defino um teto para calcular
        except:
            teto = 1000000000
        for u, ip, port, score_peer in peers:       # escolho de forma ponderada quem posso enviar chunks
            if score_peer > random.uniform(0, teto):#Testo quem vai
                peers_incentivo.append((u, ip, port))   # coloco na lista q vai ser avalida
        #print(peers_incentivo)
        for users, ip, port in peers_incentivo:            # envia para todos os peers
            nome_do_chunk, dados = escolher_chunk_compatível(user) # esolhe um chunk aleatorio
            if nome_do_chunk:                   # Se eu for capaz de enviar
                try: 
                    #print(f"[{users}] Enviando {os.path.basename(nome_do_chunk)} para {ip} : {port}")
                    enviado = send_chunk(user, ip, port, nome_do_chunk, dados)# Vai enviar para esse ip um chunk aleatorio que eu tiver e consiguir enviar
                    if enviado:                     # Se foi enviado com sucesso
                        successful_responses = 1
                        bytes_sent = len(dados)
                        time_connected += 1
                        #bytes_sent = bytes_sent//1000 # parametrizado
                        update_score(user, bytes_sent, time_connected, successful_responses)
                        #print(user,"enviando para", users)
                    else:
                        successful_responses = 0
                        time_connected += 1
                        update_score(user, 0, time_connected, successful_responses, failed_transfers=1)
                except Exception as e:
                    print(f"Não foi possível enviar para o peer {users}: {e}")
            else:                               # mesmo qie nao tenha conseguido enviar vamos dar um incentivo a ele
                bytes_sent = 10                                            # novo score pra ajudar
                break                                                       # Pois ainda nao tem pontuação suficiente para enviar

def send_chunk(user, ip, port, nome_chunk, dados):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        # Envia a requisição de chunk como JSON
        mensagem = {"enviando": nome_chunk,
                   "dados"   :  dados,
                   "sender"    : user
                   }
        enviado = json.dumps(mensagem)
        s.sendall(enviado.encode())
        s.shutdown(socket.SHUT_WR)
        #print(f"[✓] Chunk '{nome_chunk}' enviado com sucesso")
        s.close()
        return True
    except Exception as e:
        print(f"[Erro ao enviar pedaços] {e}")
        return False


#CHUNKS_FOLDER = "arquivos_cadastrados/chunkscriados/bigfile/"
CHUNKS_FOLDER_BASE = "arquivos_cadastrados/chunkscriados"
def escolher_chunk_compatível(usuario):    # Apenas para pegar um chunk aleatorio
    """Seleciona aleatoriamente um arquivo que seja menor ou igual ao limite dado."""
    pasta_usuario = os.path.join(CHUNKS_FOLDER_BASE,usuario)
    todosChunks = []

    for pasta in os.listdir(pasta_usuario):
        caminho_subpasta = os.path.join(pasta_usuario,pasta)
        if os.path.isdir(caminho_subpasta):
            for arquivo in os.listdir(caminho_subpasta):    
                if arquivo.startswith(pasta) and ".part" in arquivo:
                    todosChunks.append(os.path.join(caminho_subpasta,arquivo))
    if not todosChunks:
        return None, None
    random.shuffle(todosChunks)
    caminho_chunk = todosChunks[0]
    with open(caminho_chunk, "r") as arquivo:
        dados = arquivo.read()
    return caminho_chunk, dados               # retorna todos os dados da chunk e o caminho dele

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
        print(f"\n Mensagem enviada para {to_user} ({ip}:{port})✅\n")
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
        print("Erro ao anunciar arquivos:", e)
def announce_file_novo(username, nome_arquivo):
    """
    Divide um arquivo em chunks, calcula seu checksum e o anuncia para o tracker via socket TCP.

    Parâmetros:
        username (str): Nome do usuário que está anunciando o arquivo.
        nome_arquivo (str): Caminho do arquivo a ser dividido e anunciado.
    """
    dividir_em_chunks_user(nome_arquivo, 1024,username)
    print("O arquivo foi divido em chunks!")
    nome_pasta = os.path.splitext(nome_arquivo)[0]
    print(f"O nome_pasta é:{nome_pasta}")
    caminho_chunks = f"arquivos_cadastrados/chunkscriados/{username}/{nome_pasta}"
    json_path = caminho_chunks+"/"+nome_pasta+".json"
    #json_path = os.path.join(caminho_chunks, nome_pasta + ".json")

    with open(nome_arquivo, 'rb') as f:
        conteudo = f.read()
        checksum = hashlib.sha256(conteudo).hexdigest()

    with open(json_path, 'r') as jf:
        chunks_info = json.load(jf)

    nomes_chunks = [chunk['nome'] for chunk in chunks_info]

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
        print("Erro ao anunciar arquivo:", e)
