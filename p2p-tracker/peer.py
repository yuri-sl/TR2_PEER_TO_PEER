import socket
import json
import hashlib
import os

TRACKER_HOST = 'localhost'
TRACKER_PORT = 5000

session_token = None

def hash_file(path):
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

def send_request(data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TRACKER_HOST, TRACKER_PORT))
        s.sendall(json.dumps(data).encode())
        response = s.recv(4096)
        return json.loads(response.decode())

def register():
    username = input("Usuário: ")
    password = input("Senha: ")
    response = send_request({
        "action": "register",
        "username": username,
        "password": password
    })
    print(response.get("message"))

def login():
    global session_token
    username = input("Usuário: ")
    password = input("Senha: ")
    response = send_request({
        "action": "login",
        "username": username,
        "password": password
    })
    if response["status"] == "ok":
        session_token = response["token"]
        print("Login bem-sucedido!")
    else:
        print("Erro:", response.get("message"))

def announce():
    global session_token
    if not session_token:
        print("Você precisa fazer login antes.")
        return
    path = input("Digite o caminho do arquivo a anunciar: ").strip()
    if not os.path.isfile(path):
        print("Arquivo não encontrado.")
        return

    filename = os.path.basename(path)
    size = os.path.getsize(path)
    file_hash = hash_file(path)

    response = send_request({
        "action": "announce",
        "token": session_token,
        "files": [{
            "filename": filename,
            "size": size,
            "hash": file_hash
        }]
    })
    print(response.get("message"))

def main():
    while True:
        print("\n--- Peer Menu ---")
        print("1. Registrar")
        print("2. Login")
        print("3. Anunciar Arquivo")
        print("4. Sair")
        option = input("Escolha uma opção: ")
        if option == "1":
            register()
        elif option == "2":
            login()
        elif option == "3":
            announce()
        elif option == "4":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
