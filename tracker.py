import socket
import json
import hashlib
import os
import threading
import time 

HOST = 'localhost'
PORT = 5000
USER_LIST_PATH = 'user_list.json'
FILES_LIST_PATH = 'files.json'
session = {}
files = {}
avaiableForChat = []
avaiableForSeed = []
chunks = {}
checksunsarq = {}
import json
def carregar_arquivos_em_json(caminho_arquivo="arquivos_cadastrados/arquivos_tracker.json"):
    """Carrega e retorna o dicionário de arquivos registrados, ou retorna {} se não existir."""
    if os.path.exists(caminho_arquivo) and os.path.getsize(caminho_arquivo) > 0:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            try:
                dados = json.load(f)
                return dados
            except json.JSONDecodeError:
                # Arquivo existe mas está corrompido ou vazio
                return {}
    return {}
arquivos = carregar_arquivos_em_json()  # Novo dicionário global com info de arquivos
def salvar_arquivos_em_json():
    with open("arquivos_cadastrados/arquivos_tracker.json", "w", encoding="utf-8") as f:
        json.dump(arquivos, f, indent=4, ensure_ascii=False)

def carregar_usuarios() -> dict:
    """
    Carrega a lista de usuários a partir de um arquivo JSON.

    - Se o arquivo especificado por USER_LIST_PATH não existir, ele será criado com um dicionário vazio.
    - Se o arquivo existir, seu conteúdo será carregado e retornado como um dicionário.

    Returns:
        dict: Dicionário contendo os usuários carregados do arquivo JSON.
    """
    if not os.path.exists(USER_LIST_PATH):
        f = open(USER_LIST_PATH,'w')
        json.dump({},f)
    else:
        f = open(USER_LIST_PATH,'r')
        print("[SUCESSO]O Arquivo existe!")
        return json.load(f)

def salvar_usuarios(usuario_input) -> None:
    """
    Salva os dados dos usuários em um arquivo JSON.

    Args:
        usuario_input (dict): Dicionário contendo os dados dos usuários a serem salvos.

    O conteúdo é escrito com indentação para melhor legibilidade.
    """
    f = open(USER_LIST_PATH,'w')
    json.dump(usuario_input,f,indent=4)

def registrar_usuario(username, password) -> tuple[bool, str]:
    """
    Registra um novo usuário no sistema.

    Verifica se o nome de usuário já existe. Caso não exista, salva o novo usuário
    com a senha criptografada usando SHA-256.

    Args:
        username (str): Nome de usuário a ser registrado.
        password (str): Senha correspondente ao usuário.

    Returns:
        tuple[bool, str]: Um par (sucesso, mensagem), onde:
            - sucesso (bool): Indica se o registro foi bem-sucedido.
            - mensagem (str): Mensagem explicando o resultado da operação.
    """
    usarios_sistema = carregar_usuarios()
    if username in usarios_sistema:
        msg = "Usuário já existe cadastrado no sistema!"
        return False, msg
    hash_senha = hashlib.sha256(password.encode()).hexdigest()
    usarios_sistema[username] = {"password": hash_senha}
    salvar_usuarios(usarios_sistema)
    msg = "Usuário registrado com sucesso!"
    return True,msg

def login(username,password) -> tuple[bool, str]:
    """
    Realiza o login de um usuário verificando se as credenciais estão corretas.

    Args:
        username (str): Nome de usuário a ser autenticado.
        password (str): Senha correspondente ao usuário.

    Returns:
        tuple[bool, str]: Um par (sucesso, mensagem), onde:
            - sucesso (bool): Indica se o login foi bem-sucedido.
            - mensagem (str): Mensagem explicando o resultado da tentativa de login.
    """
    usuarios_sistema = carregar_usuarios()
    if (username not in usuarios_sistema):
        return False, "Usuário não encontrado no sistema!"
    hash_senha = hashlib.sha256(password.encode()).hexdigest()
    if(
        usuarios_sistema[username]["password"] != hash_senha
    ):
        return False,"senha incorreta!"
    return True,"Login Efetuado com sucesso!"

def carregar_arquivos() -> dict:
    """
    Carrega os dados dos arquivos a partir de um arquivo JSON.

    - Se o arquivo especificado por FILES_LIST_PATH não existir, retorna um dicionário vazio.
    - Caso o arquivo exista, seu conteúdo JSON é carregado e retornado como um dicionário.

    Returns:
        dict: Dicionário contendo os dados carregados do arquivo JSON.
    """
    if not os.path.exists(FILES_LIST_PATH):
        return {}
    f = open(FILES_LIST_PATH,'r')
    return json.load(f)

def salvar_arquivos(dados) -> None:
    """
    Salva os dados dos arquivos em um arquivo JSON.

    Args:
        dados (dict): Dicionário contendo os dados que devem ser persistidos.

    O conteúdo é salvo com indentação para facilitar a leitura manual do arquivo.
    """
    f = open(FILES_LIST_PATH,'r')
    json.dump(dados, f, indent=4)

def list_clients() -> list[str]:
    """
    Lista os nomes dos usuários cadastrados no sistema.

    Verifica se o arquivo de usuários existe e, em caso afirmativo,
    exibe e retorna a lista de nomes de usuários.

    Returns:
        list[str]: Lista com os nomes dos usuários cadastrados.
                   Retorna uma lista vazia caso o arquivo não exista.
    """
    if not os.path.exists(USER_LIST_PATH):
        print("[ERRO] Arquivo de usuários não encontrado.")
        return {}
    with open(USER_LIST_PATH, 'r') as f:
        data = json.load(f)
        lista_usuarios = list(data.keys())  # Lista de usuarios ativos
        print("[SUCESSO] Usuários cadastrados:")
        for usuario in lista_usuarios:
            print(f" - {usuario}")
        return lista_usuarios

def list_files(peers):
    return files

def protocolos_base(mensagem, client_socket) -> None:
    """
    Protocolos para clientes que não estão logados ou cadastrados
    """
    if mensagem['action'] == 'register':    # Se registrar 
        username = mensagem["username"]
        password = mensagem["password"]
        sucesso, msg = registrar_usuario(username, password)            # Bool caso aceito e a mensagem 
        print(f"[INFO] A mensagem dada pela função foi: {msg}, e o status de sucesso foi: {sucesso}")
        resposta = {"status": "ok" if sucesso else "erro", "mensagem": msg}
        client_socket.sendall(json.dumps(resposta).encode())            # resposta para o cliente
    elif mensagem['action'] == 'login':                                 # Fazer login
        username = mensagem["username"]
        password = mensagem["password"]
        sucesso,msg = login(username,password)                          # Bool caso aceito e a mensagem 
        if sucesso:
            session[username] = 0                                       # Inicia o tempo de heartbeat deste cliente
            files[username] = mensagem['files']
            user_port = mensagem['chat_port']
            user_chunk_port = mensagem['chunk_port']
            user_ip = client_socket.getpeername()[0]
            avaiableForChat.append((username,user_ip,user_port))
            avaiableForSeed.append((username,user_ip,user_chunk_port))
        print(f"[INFO] O login obteve sucesso?{sucesso}, a mensagem dada foi: {msg}")
        resposta = {"status": "ok" if sucesso else "erro", "mensagem": msg}
        client_socket.sendall(json.dumps(resposta).encode())
    else:
        resposta = {"status": "erro", "mensagem": "Ação desconhecida."}
        client_socket.sendall(json.dumps(resposta).encode())            # Caso nenhuma das acoes tenha sido aceitas

def protocolos_restritos(mensagem, client_socket) -> None:
    global arquivos
    if mensagem['action'] == 'list_clients':
        peers = list(session.keys())
        resposta = {"status": "ok", "mensagem": peers}
        client_socket.sendall(json.dumps(resposta).encode())

    elif mensagem['action'] == 'list_files':
        peers = list(session.keys())
        arquivos = list_files(peers)
        resposta = {"status": "ok", "mensagem": arquivos}
        client_socket.sendall(json.dumps(resposta).encode())

    elif mensagem['action'] == "get_peer_info":
        asked_user = mensagem['username']
        peer_found = None
        for user, ip, port in avaiableForChat:
            if asked_user == user:
                peer_found = {"ip": ip, "port": port}
                break
        if peer_found:
            resposta = {"status": "ok", "mensagem": peer_found}
        else:
            resposta = {"status": "erro", "mensagem": "Usuário não está online para operação."}
        client_socket.sendall(json.dumps(resposta).encode())

    elif mensagem['action'] == "get_peer_info_chunk":
        asked_user = mensagem['username']
        peer_found = None
        for user, ip, port in avaiableForSeed:
            if asked_user == user:
                peer_found = {"ip": ip, "port": port}
                break
        if peer_found:
            resposta = {"status": "ok", "mensagem": peer_found}
        else:
            resposta = {"status": "erro", "mensagem": "Usuário não está online para operação."}
        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == "get_ip":
        asked_user = mensagem['username']
        if not avaiableForChat:
            peer_found = None
        else:
            peer_found = True
        if peer_found:
            resposta = {"status": "ok", "mensagem": avaiableForChat}
        else:
            resposta = {"status": "erro", "mensagem": "Usuário não está online para operação."}
        client_socket.sendall(json.dumps(resposta).encode())

    elif mensagem['action'] == 'heartbeat':
        user = mensagem['username']
        if user in session:
            session[user] = 0
            resposta = {"status": "ok", "mensagem": "Heartbeat recebido"}
        else:
            resposta = {"status": "erro", "mensagem": "Usuário desconectado"}
        client_socket.sendall(json.dumps(resposta).encode())

    elif mensagem['action'] == 'update_files':
        username = mensagem['username']
        novos_arquivos = mensagem['files']
        if username in session:
            files[username] = novos_arquivos
            print(f"[Tracker] Arquivos atualizados: ", files)
            resposta = {"status": "ok", "mensagem": f"{len(novos_arquivos)} arquivo(s) anunciado(s) com sucesso!"}
        else:
            resposta = {"status": "erro", "mensagem": "Usuário não está logado"}
        client_socket.sendall(json.dumps(resposta).encode())

    elif mensagem['action'] == 'register_chunks':
        try:
            global chunks
            chunks[mensagem['username']] = mensagem['chunk']
            resposta = {"status": "ok", "mensagem": f"chunk(s) anunciado(s) com sucesso!"}
        except:
            resposta = {"status": "erro", "mensagem": f"Usuário não está logado"}
        client_socket.sendall(json.dumps(resposta).encode())

    elif mensagem['action'] == 'register_arq':
        try:
            global checksunsarq
            if mensagem['username'] not in checksunsarq:
                checksunsarq[mensagem['username']] = []
            checksunsarq[mensagem['username']] = mensagem['checksunsarq']
            resposta = {"status": "ok", "mensagem": f"arquivo registrado com sucesso!"}
        except:
            resposta = {"status": "erro", "mensagem": f"Usuário não está logado"}
        client_socket.sendall(json.dumps(resposta).encode())

    elif mensagem['action'] == 'reassembly':
        try:
            lista = checksunsarq[mensagem['username']]
            arquivo = mensagem['arquivo'] + ".txt"
            checksum = None
            for a in lista:
                if a[0] == arquivo:
                    checksum = a[1]
                    break
            if checksum:
                resposta = {"status": "ok", "mensagem": f"chunk(s) anunciado(s) com sucesso!", "checksum": checksum}
            else:
                resposta = {"status": "erro", "mensagem": "arquivo nao existe"}
        except:
            resposta = {"status": "erro", "mensagem": "Usuário não está logado"}
        client_socket.sendall(json.dumps(resposta).encode())

    elif mensagem['action'] == 'announce_file':
        try:
            dados_arquivo = mensagem['arquivo']
            nome_arquivo = dados_arquivo['nome']
            username = mensagem['username']

            if nome_arquivo not in arquivos:
                arquivos[nome_arquivo] = {
                    "checksum": dados_arquivo['checksum'],
                    "chunks_path": dados_arquivo['chunks_path'],
                    "chunks": dados_arquivo['chunks'],
                    "donos": [username]
                }
            else:
                if username not in arquivos[nome_arquivo]['donos']:
                    arquivos[nome_arquivo]['donos'].append(username)

            resposta = {"status": "ok", "mensagem": f"Arquivo '{nome_arquivo}' anunciado com sucesso."}
            print("\n=== Estado atual de arquivos antes de salvar ===")
            print(json.dumps(arquivos, indent=2))
            salvar_arquivos_em_json()
        except Exception as e:
            resposta = {"status": "erro", "mensagem": f"Erro ao anunciar arquivo: {str(e)}"}
        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == 'update_user_list':
        try:
            novos_usuarios_online = set(mensagem.get('peers_online', []))

            if not isinstance(novos_usuarios_online, set):
                raise ValueError("'peers_online' deve ser uma lista.")

            # Carrega o estado atual
            if os.path.exists("usuarios_online.json"):
                with open("usuarios_online.json", "r") as f:
                    estado_atual = set(json.load(f))
            else:
                estado_atual = set()

            # Substitui pelos novos
            estado_atual = estado_atual.intersection(novos_usuarios_online).union(novos_usuarios_online)

            # Escreve o novo estado limpo (sem usuários offline)
            with open("usuarios_online.json", "w") as f:
                json.dump(sorted(list(estado_atual)), f, indent=4)

            resposta = {"status": "ok", "mensagem": "Lista de usuários online atualizada com sucesso."}

        except Exception as e:
            resposta = {"status": "erro", "mensagem": f"Erro ao atualizar a lista de usersAtivos: {str(e)}"}

        client_socket.sendall(json.dumps(resposta).encode())

    
    elif mensagem['action'] == 'verify_missing_chunks':
        try:
            username = mensagem['username']           # Ex: "F"
            nome_arquivo = mensagem['nome_arquivo']   # Ex: "Kal"

            base_chunks_path = "chunkscriados"
            received_chunks_path = f"chunks_recebidos/{username}/{nome_arquivo}"

            # Conjunto de todos os chunks disponíveis por outros peers
            chunks_disponiveis = set()

            # Itera sobre todas as pastas (usuários) em chunkscriados
            for pasta_usuario in os.listdir(base_chunks_path):
                if pasta_usuario == username:
                    continue  # ignora a própria pasta do usuário

                caminho_usuario = os.path.join(base_chunks_path, pasta_usuario)
                for pastas_arquivos in os.listdir(caminho_usuario):

                    if os.path.isdir(caminho_usuario):
                        arquivos = [
                            arq for arq in os.listdir(caminho_usuario)
                            if os.path.isfile(os.path.join(caminho_usuario, arq))
                        ]
                        chunks_disponiveis.update(arquivos)

            # Chunks que o usuário já possui
            chunks_usuario = []
            if os.path.exists(received_chunks_path):
                chunks_usuario = [
                    f for f in os.listdir(received_chunks_path)
                    if os.path.isfile(os.path.join(received_chunks_path, f))
                ]

            # Verifica chunks faltantes
            chunks_faltando = sorted(list(chunks_disponiveis - set(chunks_usuario)))

            resposta = {
                "status": "ok",
                "mensagem": f"Verificação realizada para '{nome_arquivo}'.",
                "chunks_faltando": chunks_faltando,
                "chunks_recebidos": sorted(chunks_usuario),
                "chunks_disponiveis_outros_peers": sorted(list(chunks_disponiveis))
            }

        except Exception as e:
            resposta = {"status": "erro", "mensagem": f"Erro ao verificar chunks faltantes: {str(e)}"}

        client_socket.sendall(json.dumps(resposta).encode())
    #elif mensagem['action'] == "update_online_owners":
    #    try:
    elif mensagem['action'] == "get_chunk_owners_online":
            nome_arquivo = mensagem.get("arquivo")
            solicitante = mensagem.get("username")
            chunks_info = {}
            path_base = "arquivos_cadastrados/chunkscriados"

            try:
                with open("usuarios_online.json", "r") as f:
                    online_users = set(json.load(f))

                for usuario in os.listdir(path_base):
                    if not os.path.isdir(os.path.join(path_base, usuario)):
                        continue

                    json_path = os.path.join(path_base, usuario, nome_arquivo, f"{nome_arquivo}.json")
                    if not os.path.exists(json_path):
                        continue

                    with open(json_path, "r") as f:
                        chunks = json.load(f)
                        for chunk in chunks:
                            nome = chunk["nome"]
                            donos = chunk.get("detentores_chunk", [])
                            donos_online = [d for d in donos if d in online_users]
                            if donos_online:
                                chunks_info[nome] = donos_online

                resposta = {"status": "ok", "chunks": chunks_info}

            except Exception as e:
                resposta = {"status": "erro", "mensagem": str(e)}

            client_socket.sendall(json.dumps(resposta).encode())


    else:
        resposta = {"status": "erro", "mensagem": "Ação desconhecida ou não está logado."}
        client_socket.sendall(json.dumps(resposta).encode())

def handle_clients(client_socket, addr) -> None:
    """
    Manipula a conexão de um cliente.

    Essa função:
    - Recebe uma mensagem completa do cliente via socket;
    - Decodifica a mensagem como JSON;
    - Identifica a ação desejada (login, registro, exit, etc);
    - Encaminha o processamento para os protocolos apropriados;
    - Fecha a conexão ao final da comunicação.

    Args:
        client_socket (socket.socket): O socket da conexão com o cliente.
        addr (tuple): Endereço IP e porta do cliente (host, port).
    """
    try:
        buffer = b""                        # Acumula a mensagem recebida
        while True:
            chunk = client_socket.recv(4096)# Recebe a mensagem
            if not chunk:                   # Se estiver vazia terminou a mensagem
                break
            buffer += chunk                 # Vai juntando a mensagem

        data = buffer.decode()              # Decodifica a mensagem
        if data:                            # Se tiver decodificado tenta 
            try:
                mensagem = json.loads(data)
                user = mensagem['username'] # Nome do usuario
                print(f"[INFO] Entrou no Try. Mensagem recebida foi: {mensagem}")
                if mensagem['action'] == 'exit' and user in session:# Sai da sessao caso esteja conectado
                    session.pop(user, None)                         # Nao e mais um peers ativo
                    files.pop(user, None)                         # Nao e mais um peers ativo update_user_list
                elif user in session:                               # Se estiver logado pode continuar
                    session[user] = 0                               # Renova o tempo do usuario
                    protocolos_restritos(mensagem, client_socket)
                elif user in session and (mensagem['action'] == 'get_ip' or 
                                          mensagem['action'] == 'list_files' or
                                          mensagem['action'] == 'heartbeat'
                                          ):                               # Se estiver logado pode continuar
                    protocolos_restritos(mensagem, client_socket)
                else:                                               # Se nao tem que registrar ou logar
                    protocolos_base(mensagem, client_socket)
            except Exception as e:                                  # Caso algum deles de errado sai com msg de erro
                client_socket.sendall(json.dumps({"status": "erro", "mensagem": str(e)}).encode())
        client_socket.close()                                       # Sempre fecha a conexao 
        print(f"[INFO] Conexão encerrada com {addr}")
    except Exception as e:                                          # Caso nao consiga conectar com o cliente
        print(f"[ERRO] Erro na conexão com {addr}: {e}")

#def heartbeat(s) -> None:
#    """
#    Manipula o heartbeat de um cliente.
#
#    Args:
#        s : nome do cliente
#    """
#    while True:
#        time.sleep(1)
#        for u in list(s.keys()):                                    # copia as chaves para evitar erro de modificação durante iteração
#            if s[u] >= 300:
#                print(f"Removendo {u} por inatividade")
#                s.pop(u, None)                                      # Remove usuário inativo
#
##            else:
 #               s[u] += 1                                           # Incrementa contador de tempo
 #               print(f"{u,s[u]}")                                  # Retirar depois
def atualizar_detentores_online_em_todos(active_peers):
    print("[INFO] Iniciando atualização de detentores_online e detentores_chunk...")
    path_base = "arquivos_cadastrados/chunkscriados"

    try:
        with open("usuarios_online.json", "r", encoding="utf-8") as f:
            usuarios_online = set(json.load(f))
            print("[SUCESSO] Carregados usuários online:", usuarios_online)
    except Exception as e:
        print(f"[ERRO] Erro ao carregar usuarios_online.json: {e}")
        return

    for usuario in os.listdir(path_base):
        if usuario not in active_peers:
            continue

        caminho_usuario = os.path.join(path_base, usuario)
        if not os.path.isdir(caminho_usuario):
            continue
        print(f"[INFO] Processando: {caminho_usuario}")

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

                    for chunk in chunks_info:
                        # Garante que o dono do diretório esteja como detentor
                        detentores = chunk.get("detentores_chunk", [])
                        if usuario not in detentores:
                            detentores.append(usuario)
                        chunk["detentores_chunk"] = detentores

                        # Atualiza os detentores online
                        chunk["detentores_online"] = [p for p in detentores if p in usuarios_online]
                        chunk["quantidade_detentores_online"] = len(chunk["detentores_online"])

                    with open(caminho_json, "w", encoding="utf-8") as f:
                        json.dump(chunks_info, f, indent=4)

                    print(f"[INFO] Atualizado: {caminho_json}")

                except Exception as e:
                    print(f"[ERRO] Erro ao processar {caminho_json}: {e}")


def heartbeat(s: dict) -> None:
    while True:
        time.sleep(1)
        usuarios_online = []
        print("[INFO] Heartbeat funcionando!")

        for u in list(s.keys()):
            if s[u] >= 15:
                print(f"[INFO] Removendo {u} por inatividade")
                s.pop(u, None)
            else:
                s[u] += 1
                usuarios_online.append(u)

        try:
            with open("usuarios_online.json", "w") as f:
                json.dump(sorted(usuarios_online), f, indent=4)
        except Exception as e:
            print(f"[ERRO] Erro ao salvar usuarios_online.json: {e}")

        # 🔁 Atualiza arquivos de chunk com base nos online atuais
        atualizar_detentores_online_em_todos(usuarios_online)


def start_tracker() -> None:                                        # Inicia o server
    """
    Inicia o servidor tracker responsável por coordenar os peers.

    - Cria uma thread em segundo plano para monitoramento (heartbeat) das sessões ativas.
    - Inicia um servidor TCP que escuta por conexões de clientes (peers).
    - Para cada cliente que se conecta, uma nova thread é criada para lidar com a comunicação.

    Essa função roda indefinidamente até que o processo seja interrompido.
    """
    heartbeatpeers = threading.Thread(target=heartbeat, args=(session,), daemon = True) # Uma thread comeca a resolver 
    heartbeatpeers.start()                                              # Começa a thread
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Conexão TCP
    server_socket.bind((HOST, PORT))                                    # Conexão no host 'localhost' e porta 5000
    server_socket.listen()                                              # Espera a conexão
    print(f"[TRACKER] INICIADO EM: {HOST}:{PORT}")                      

    while True:
        client_socket, addr = server_socket.accept()                    # Aguarda os peers
        print(f"[+] Nova conexão de {addr}")                            
        thread = threading.Thread(target=handle_clients, args=(client_socket, addr)) # Uma thread comeca a resolver 
        thread.start()      # Começa a thread

if __name__ == "__main__":
    start_tracker()         # INIT

