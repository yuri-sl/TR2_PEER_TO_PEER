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
arquivos = {}  # Novo dicionário global com info de arquivos
import json

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
        print("O Arquivo existe!")
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
        print("Arquivo de usuários não encontrado.")
        return {}
    with open(USER_LIST_PATH, 'r') as f:
        data = json.load(f)
        lista_usuarios = list(data.keys())  # Lista de usuarios ativos
        print("Usuários cadastrados:")
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
        print(f"A mensagem dada pela função foi: {msg}, e o status de sucesso foi: {sucesso}")
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
        print(f"O login obteve sucesso?{sucesso}, a mensagem dada foi: {msg}")
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
            salvar_arquivos_em_json()
        except Exception as e:
            resposta = {"status": "erro", "mensagem": f"Erro ao anunciar arquivo: {str(e)}"}
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
                print(f"Entrou no Try. Mensagem recebida foi: {mensagem}")
                if mensagem['action'] == 'exit' and user in session:# Sai da sessao caso esteja conectado
                    session.pop(user, None)                         # Nao e mais um peers ativo
                    files.pop(user, None)                         # Nao e mais um peers ativo
                elif user in session:                               # Se estiver logado pode continuar
                    session[user] = 0                               # Renova o tempo do usuario
                    protocolos_restritos(mensagem, client_socket)
                else:                                               # Se nao tem que registrar ou logar
                    protocolos_base(mensagem, client_socket)
            except Exception as e:                                  # Caso algum deles de errado sai com msg de erro
                client_socket.sendall(json.dumps({"status": "erro", "mensagem": str(e)}).encode())
        client_socket.close()                                       # Sempre fecha a conexao 
        print(f"Conexão encerrada com {addr}")
    except Exception as e:                                          # Caso nao consiga conectar com o cliente
        print(f"Erro na conexão com {addr}: {e}")

def heartbeat(s) -> None:
    """
    Manipula o heartbeat de um cliente.

    Args:
        s : nome do cliente
    """
    while True:
        time.sleep(1)
        for u in list(s.keys()):                                    # copia as chaves para evitar erro de modificação durante iteração
            if s[u] >= 300:
                print(f"Removendo {u} por inatividade")
                s.pop(u, None)                                      # Remove usuário inativo

            else:
                s[u] += 1                                           # Incrementa contador de tempo
                print(f"{u,s[u]}")                                  # Retirar depois

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

