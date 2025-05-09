import socket
import json
import hashlib
import os
import threading

HOST = 'localhost'
PORT = 5000
USER_LIST_PATH = 'user_list.json'
FILES_LIST_PATH = 'files.json'
session = []

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

def list_files():
    print("ok")

def protocolos_base(mensagem, client_socket):
    if mensagem['action'] == 'register':    # Se registrar 
        username = mensagem["username"]
        password = mensagem["password"]
        sucesso, msg = registrar_usuario(username, password)
        print(f"A mensagem dada pela função foi: {msg}, e o status de sucesso foi: {sucesso}")
        resposta = {"status": "ok" if sucesso else "erro", "mensagem": msg}
        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == 'login':     # Fazer login
        username = mensagem["username"]
        password = mensagem["password"]
        sucesso,msg = login(username,password)
        if sucesso:
            session.append(username)
        print(f"O login obteve sucesso?{sucesso}, a mensagem dada foi: {msg}")
        resposta = {"status": "ok" if sucesso else "erro", "mensagem": msg}
        client_socket.sendall(json.dumps(resposta).encode())
    else:
        resposta = {"status": "erro", "mensagem": "Ação desconhecida."}
        client_socket.sendall(json.dumps(resposta).encode())

def protocolos_restritos(mensagem, client_socket):  # Apenas se tiver login
    if mensagem['action'] == 'list_clients':        # Saber quem sao os peers ativos
        peers = list_clients()
        resposta = {"status": "ok", "mensagem": peers}
        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == 'list_files':        # Saber quais arquivos estao disponiveis
        list_files()
    else:
        resposta = {"status": "erro", "mensagem": "Ação desconhecida."}
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
                    session.remove(user)                            # Nao e mais um peers ativo
                elif user in session:                               # Se estiver logado pode continuar
                    protocolos_restritos(mensagem, client_socket)
                else:                                               # Se nao tem que registrar ou logar
                    protocolos_base(mensagem, client_socket)
            except Exception as e:                                  # Caso algum deles de errado sai com msg de erro
                client_socket.sendall(json.dumps({"status": "erro", "mensagem": str(e)}).encode())
        client_socket.close()                                       # Sempre fecha a conexao 
        print(f"Conexão encerrada com {addr}")
    except Exception as e:                                          # Caso nao consiga conectar com o cliente
        print(f"Erro na conexão com {addr}: {e}")

def start_tracker():                                                    # Inicia o server
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

