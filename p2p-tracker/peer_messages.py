import socket
import threading
import json
from datetime import datetime

def start_peer_server(chat_port, meu_username):
    def handle_connection(conn, addr):
        try:
            buffer = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buffer += chunk

            mensagem = json.loads(buffer.decode())
            print(f"\n📩 Nova mensagem de {mensagem['from']}:")
            print(f"   {mensagem['message']} ({mensagem['timestamp']})\n")
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

    threading.Thread(target=server_loop, daemon=True).start()

def send_message_to_peer(ip, port, from_user, to_user, text):
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
        print(f"\n✅ Mensagem enviada para {to_user} ({ip}:{port})\n")
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
