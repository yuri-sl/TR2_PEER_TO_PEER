import socket
import threading
import json
import hashlib
import uuid

users = {}       # username -> {"password_hash": ..., "files": [...]}
files = {}       # filename -> {"hash": ..., "size": ..., "peers": [...]}
sessions = {}    # token -> username

HOST = 'localhost'
PORT = 5000

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def handle_client(conn, addr):
    print(f"[+] Conexão de {addr}")
    with conn:
        data = conn.recv(4096).decode()
        if not data:
            return
        try:
            request = json.loads(data)
            action = request.get("action")

            if action == "register":
                username = request["username"]
                password = request["password"]
                if username in users:
                    response = {"status": "error", "message": "Usuário já existe"}
                else:
                    users[username] = {"password_hash": hash_password(password), "files": []}
                    response = {"status": "ok", "message": "Registrado com sucesso"}

            elif action == "login":
                username = request["username"]
                password = request["password"]
                user = users.get(username)
                if user and user["password_hash"] == hash_password(password):
                    token = str(uuid.uuid4())
                    sessions[token] = username
                    response = {"status": "ok", "token": token}
                else:
                    response = {"status": "error", "message": "Credenciais inválidas"}

            elif action == "announce":
                token = request.get("token")
                if token not in sessions:
                    response = {"status": "error", "message": "Token inválido"}
                else:
                    username = sessions[token]
                    for file in request["files"]:
                        filename = file["filename"]
                        file_hash = file["hash"]
                        size = file["size"]

                        # Adiciona arquivo ao peer
                        users[username]["files"].append(file)

                        # Registra no dicionário global
                        if filename not in files:
                            files[filename] = {"hash": file_hash, "size": size, "peers": [username]}
                        else:
                            if username not in files[filename]["peers"]:
                                files[filename]["peers"].append(username)

                    response = {"status": "ok", "message": "Arquivos anunciados com sucesso"}

            else:
                response = {"status": "error", "message": "Ação desconhecida"}

        except Exception as e:
            response = {"status": "error", "message": f"Erro no servidor: {str(e)}"}

        conn.sendall(json.dumps(response).encode())

def start_tracker():
    print(f"[TRACKER] Rodando em {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_tracker()
