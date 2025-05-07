import socket
import json
import hashlib
import os
import threading

HOST = 'localhost'
PORT = 5000
USER_LIST_PATH = 'user_list.json'
FILES_LIST_PATH = 'files.json'


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
    print("ok")

def list_files():
    print("ok")

def protocolos_aceitos(mensagem, client_socket):
    if mensagem['action'] == 'register':
        username = mensagem["username"]
        password = mensagem["password"]
        sucesso, msg = registrar_usuario(username, password)
        print(f"A mensagem dada pela função foi: {msg}, e o status de sucesso foi: {sucesso}")
        resposta = {"status": "ok" if sucesso else "erro", "mensagem": msg}
        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == 'login':
        username = mensagem["username"]
        password = mensagem["password"]
        sucesso,msg = login(username,password)
        print(f"O login obteve sucesso?{sucesso}, a mensagem dada foi: {msg}")
        client_socket.sendall(json.dumps(resposta).encode())
    elif mensagem['action'] == 'list_clients':
        list_clients()
    elif mensagem['action'] == 'list_files':
        list_files()
    else:
        resposta = {"status": "erro", "mensagem": "Ação desconhecida."}
        client_socket.sendall(json.dumps(resposta).encode())

def start_tracker(client_socket, addr):
    try:
        buffer = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            buffer += chunk

        data = buffer.decode()
        if data:
            try:
                mensagem = json.loads(data)
                print(f"Entrou no Try. Mensagem recebida foi: {mensagem}")
                protocolos_aceitos(mensagem, client_socket)
            except Exception as e:
                client_socket.sendall(json.dumps({"status": "erro", "mensagem": str(e)}).encode())
    except Exception as e:
        print(f"Erro na conexão com {addr}: {e}")
    finally:
        client_socket.close()
        print(f"Conexão encerrada com {addr}")

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[TRACKER] INICIADO EM: {HOST}:{PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[+] Nova conexão de {addr}")
        thread = threading.Thread(target=start_tracker, args=(client_socket, addr))
        thread.start()

