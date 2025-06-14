import socket
import threading
import json
from datetime import datetime
import os
from main_file import *

def start_peer_server(chat_port, meu_username) -> None:
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
            want = mensagem["chunk"]
            if want:
                entregar_chunk_desejado(mensagem)
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

def entregar_chunk_desejado(mensagem):
    user = mensagem["from"]
    usuario_logado = mensagem["to"]
    dados_start_chat = {
        "action":"get_peer_info",
        "username": user
    }
    resposta_start_chat = send_to_tracker(dados_start_chat)
    chunk_desejado = mensagem["message"]
    if resposta_start_chat.get("status")=="ok":
        peer_info = resposta_start_chat.get("mensagem",{})
        peer_ip = peer_info.get("ip")
        peer_port = peer_info.get("port")
        wantchunk = False
        print(f"Iniciando a conversa com {user} em {peer_ip}:{peer_port}")
        print(f"Digite a sua mensagem para falar com {user}:")
        texto = input("Digite sua mensagem:")
        send_message_to_peer(peer_ip, peer_port, usuario_logado, user, texto, wantchunk)
def send_message_to_peer(ip, port, from_user, to_user, text, wantchunk) -> None:
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
        "chunk" : wantchunk,
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
    Permite ao usuário selecionar arquivos .py locais para anunciar ao tracker.

    - Lista todos os arquivos .py no diretório atual.
    - Solicita ao usuário que escolha quais arquivos deseja anunciar, indicando índices.
    - Envia a lista selecionada ao tracker na ação "update_files".
    - Recebe e exibe a resposta do servidor.

    Args:
        username (str): Nome de usuário que está anunciando os arquivos.
    """
    print("\n Escolha quais arquivos para anunciar (apenas arquivos.py são listados)")
    all_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py')]

    if not all_files:
        print("Nenhum arquivo .py encontrado")
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