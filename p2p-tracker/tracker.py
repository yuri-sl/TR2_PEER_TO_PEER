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
chunks = {}

def carregar_usuarios():
    if not os.path.exists(USER_LIST_PATH):
        f = open(USER_LIST_PATH,'w')
        json.dump({},f)
    else:
        f = open(USER_LIST_PATH,'r')
        print("O Arquivo existe!")
        return json.load(f)

def salvar_usuarios(usuario_input):
    f = open(USER_LIST_PATH,'w')
    json.dump(usuario_input,f,indent=4)

def registrar_usuario(username, password):
    usarios_sistema = carregar_usuarios()
    if username in usarios_sistema:
        msg = "Usuário já existe cadastrado no sistema!"
        return False, msg
    hash_senha = hashlib.sha256(password.encode()).hexdigest()
    usarios_sistema[username] = {"password": hash_senha}
    salvar_usuarios(usarios_sistema)
    msg = "Usuário registrado com sucesso!"
    return True,msg

def login(username,password):
    usuarios_sistema = carregar_usuarios()
    if (username not in usuarios_sistema):
        return False, "Usuário não encontrado no sistema!"
    hash_senha = hashlib.sha256(password.encode()).hexdigest()
    if(
        usuarios_sistema[username]["password"] != hash_senha
    ):
        return False,"senha incorreta!"
    return True,"Login Efetuado com sucesso!"

def carregar_arquivos():
    if not os.path.exists(FILES_LIST_PATH):
        return {}
    f = open(FILES_LIST_PATH,'r')
    return json.load(f)

def salvar_arquivos(dados):
    f = open(FILES_LIST_PATH,'r')
    json.dump(dados, f, indent=4)

def list_clients():
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
"""
def map_files_to_peers(peers):
    arquivo_para_peers = {}
    for peer, arquivos in peers.items():
        for arquivo in arquivos:
            if arquivo not in arquivo_para_peers:
                arquivo_para_peers[arquivo] = []
            arquivo_para_peers[arquivo].append(peer)
    return arquivo_para_peers
"""
def protocolos_base(mensagem, client_socket):
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
            user_ip = client_socket.getpeername()[0]
            avaiableForChat.append((username,user_ip,user_port))
        print(f"O login obteve sucesso?{sucesso}, a mensagem dada foi: {msg}")
        resposta = {"status": "ok" if sucesso else "erro", "mensagem": msg}
        client_socket.sendall(json.dumps(resposta).encode())
    else:
        resposta = {"status": "erro", "mensagem": "Ação desconhecida."}
        client_socket.sendall(json.dumps(resposta).encode())            # Caso nenhuma das acoes tenha sido aceitas

def protocolos_restritos(mensagem, client_socket):  # Apenas se tiver login
    if mensagem['action'] == 'list_clients':        # Saber quem sao os peers ativos
        #peers = list_clients()
        peers = list(session.keys())
        resposta = {"status": "ok", "mensagem": peers}
        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == 'list_files':        # Saber quais arquivos estao disponiveis
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
            resposta = {"status": "erro", "mensagem": "Usuário não está online para chat."}

        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == 'heartbeat':
        user = mensagem['username']
        if user in session:
            session[user] = 0
            resposta = {"status":"ok","mensagem":"Heartbeat recebido"}
        else:
            resposta = {"status":"erro","mensagem":"Usuário desconectado"}
        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == 'update_files':
        username = mensagem['username']
        novos_arquivos = mensagem['files']
        if username in session:
            files[username] = novos_arquivos
            print(f"[Tracker] Arquivos atualizados: ",files)
            resposta = {"status": "ok", "mensagem": f"{len(novos_arquivos)} arquivo(s) anunciado(s) com sucesso!"}
        else:
            resposta = {"status": "erro", "mensagem": "Usuário não está logado"}
        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == 'register_chunks':
        for i in mensagem['chunk']:
            chunks[mensagem['username']] = mensagem['chunk']

#       print("ação recebida!!!")
#        asked_user = mensagem['username']
#        peer_found = None
#        asked_port = 0
#        for user,port in avaiableForChat:
#            if asked_user == user:
#                peer_found = {"ip":addr[0],"port":port}
#                break
#           if peer_found:
#                resposta = {"status":"ok",
#                            "mensagem":peer_found}
#            else:
#                resposta = {"status":"erro","mensagem":
#                            "user n existe para chat"}
#            client_socket.sendall(json.dumps(resposta).encode())
        #for tuples in avaiableForChat:
        #    userLogged = tuples[0]
        #    if(asked_user==userLogged):
        #        print("USER FOUND!!")
        #        asked_port = tuples[1]

#        if asked_port!=0:
#            print("YOU CAN TALK WITH THIS PERSON!")
#        else:
#            print("YOU CAN NOT TALK WITH THIS PERSON!")


    else:
        resposta = {"status": "erro", "mensagem": "Ação desconhecida ou não esta logado."}
        client_socket.sendall(json.dumps(resposta).encode())
def handle_clients(client_socket, addr):
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

def heartbeat(s):
    while True:
        time.sleep(1)
        for u in list(s.keys()):                                    # copia as chaves para evitar erro de modificação durante iteração
            if s[u] >= 600000:
                print(f"Removendo {u} por inatividade")
                s.pop(u, None)                                      # Remove usuário inativo

            else:
                s[u] += 1                                           # Incrementa contador de tempo
                print(f"{u,s[u]}")                                  # Retirar depois

def start_tracker():                                                    # Inicia o server
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

