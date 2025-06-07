from tracker import *
import subprocess
import sys
import os
import socket
import json
import random
from peer_messages import *
import platform
import platform
import shutil
from peer import *

menu_1 = "MENU PRINCIPAL \n1 - Registrar;\n2 - Login no Sistema;\n3 - Sair do sistema;"
menu_2 = "\n4 - Anunciar um Arquivo;\n5 - Listagem de Peers Ativos;\n6 - Iniciar Chat com Peer;\n7 - Sair do Sistema;\n8 - Anunciar arquivos manualmente;\n9 - Anunciar todos os chunks;"


def launch_tracker_cross_platform():
    null = subprocess.DEVNULL
    system = platform.system()
    if system == 'Windows':
        subprocess.Popen(['start', 'cmd', '/k', 'python tracker.py'], shell=True)
    elif system == 'Linux':
        if shutil.which('gnome-terminal'):
            subprocess.Popen(['gnome-terminal', '--', 'python3', 'tracker.py'], stderr=null)
        elif shutil.which('xterm'):
            subprocess.Popen(['xterm', '-hold', '-e', 'python3 tracker.py'], stderr=null)
        elif shutil.which('konsole'):
            subprocess.Popen(['konsole', '-e', 'python3 tracker.py'], stderr=null)
        else:
            subprocess.Popen(['python3', 'tracker.py'], stderr=null)

def send_to_tracker(data):
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
def start_heartbeat(username):
    def loop():
        time.sleep(1)  # <- aqui: espera o login ser processado no Tracker
        while True:
            try:
                dados = {"action": "heartbeat", "username": username}
                resposta = send_to_tracker(dados)
                if resposta.get("status") != "ok":
                    print("⚠️ Você foi desconectado por inatividade. Faça login novamente.")
                    os._exit(1)
                time.sleep(600000)
            except:
                print("⚠️ Erro de conexão no heartbeat. Encerrando cliente.")
                os._exit(1)
    threading.Thread(target=loop, daemon=True).start()

def salvar_mensagem(usuario_remetente,destinatario,mensagem,caminho_arquivo = "messages_list.json"):
    registro_mensagem = {
        "usuario_remetente":usuario_remetente,
        "usuario_destinatario":destinatario,
        "mensagem":mensagem
    }

    mensagens_salvas = []

    if os.path.exists(caminho_arquivo):
        try:
            f = open(caminho_arquivo,"r",encoding="utf-8")
            conteudo = f.read().strip()
            if conteudo:
                dados = json.loads(conteudo)
                if isinstance(dados,list):
                    mensagens_salvas = dados
                else:
                    print("Formato inválido detectado em messages_list.json. Substituindo por lista.")
            else:
                print("Arquivo vazio, criando nova lista de mensagens")
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}. Reiniciando arquivo.")
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}. Reiniciando arquivo.")
    mensagens_salvas.append(registro_mensagem)

    f = open(caminho_arquivo,"w",encoding="utf-8")
    json.dumps(mensagens_salvas,f,indent=4,ensure_ascii=False)

        

def is_tracker_running(host = 'localhost',port=5000):
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((host,port))
        s.close()
        return True
    except ConnectionRefusedError:
        return False

def interactiveMenu_1():
    usuario_logado = None
    chat_port = 5000 + random.randint(1,1000)
    os.system('cls||clear')

    while True:
        os.system('cls||clear')
        print(menu_1)
        operation = input("insira a sua operação desejada:\n")

        if operation == "1":
            usernameRegister = input("Defina seu nome de usuário: ")
            passwordRegister = input("Defina a sua senha: ")
            confirm_password = input("Confirme a sua senha: ")
            if passwordRegister != confirm_password:
                print("Senhas não coincidiram!")
                input("Aperte Enter para continuar")
                continue
            print("Passou adiante!")
            dados = {
                "action": "register",
                "username": usernameRegister,
                "password": passwordRegister
            }
            print("JSon gerado!")
            resposta = send_to_tracker(dados)
            print("Chegou resposta!!")

            print(resposta["mensagem"])
            input("Pressione enter para continuar")
            os.system('cls||clear')

        elif operation == "2":
            username_login = input("Insira o seu nome de usuário: ")
            password = input("Insira sua senha: ")
            arquivos = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py')]
            dados = {
                "action": "login",
                "username": username_login,
                "password": password,
                "files"   : arquivos,
                "chat_port": chat_port
            }
            resposta = send_to_tracker(dados)
            print("Resposta recebida!")
            #print(resposta)

            if resposta.get("status") == "ok":
                print(resposta["mensagem"])
                usuario_logado = username_login
                start_peer_server(chat_port,usuario_logado)
                start_heartbeat(usuario_logado)
                break  # break the first menu loop and go to the second
            if resposta.get("status") == "erro":
                print("Erro - ",resposta['mensagem'])
            input("Pressione enter para continuar")
            os.system('cls||clear')

        elif operation == "3":
            print("Bye Bye!!")
            exit()
            return False
        else:
            print("Operação inválida!")
            input("Pressione Enter para continuar")
            os.system('cls||clear')

    # Now you're logged in (usuario_logado is set)
    while usuario_logado:
        os.system('cls||clear') #Limpar o diretório
        print(menu_2)
        operation = input("insira a sua operação desejada:\n")

        if operation == "4":
            try:
                dados = {
                    "action": "list_files",
                    "username": usuario_logado
                }
                resposta = send_to_tracker(dados)
                print("Arquivos dos Peers Ativos: ")
                print(resposta["mensagem"])
                print(files)
                input("Pressione Enter para continuar")
                os.system('cls||clear')
            except:
                print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")

        elif operation == "5":
            try:
                dados = {
                    "action": "list_clients",
                    "username": usuario_logado
                }
                resposta = send_to_tracker(dados)
                print("Peers Ativos: ")
                for peer in resposta.get("mensagem", []):
                    if(peer == usuario_logado):
                        print(f" - {peer} (Você)")
                    else:
                        print(f" - {peer}")
                input("Pressione Enter para continuar")
                os.system('cls||clear')
            except:
                print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")
        elif operation == "6":
            try:
                dados = {
                    "action": "list_clients",
                    "username": usuario_logado
                }
                resposta = send_to_tracker(dados)
                print("Peers Ativos: ")
                i = 0
                for peer in resposta.get("mensagem", []):
                    i += 1
                    if(peer == usuario_logado):
                        print(f"[{i}] - {peer} (Você)")
                    else:
                        print(f"[{i}] - {peer}")
                accept_chat = input(("Gostaria de comunicar com um Peer?\n1-Sim    0-Não\n"))
                if accept_chat == "1":
                    selected_user = input("Digite o nome do usuário que deseja falar com\n")
                    i = 0
                    for user in resposta.get("mensagem",[]):
                        i += 1
                        if selected_user == user or str(i) == selected_user:
                            print("Usuário Escolhido para conversar com sucesso!")
                            dados_start_chat = {
                                "action":"get_peer_info",
                                "username": user
                            }
                            resposta_start_chat = send_to_tracker(dados_start_chat)

                            if resposta_start_chat.get("status")=="ok":
                                peer_info = resposta_start_chat.get("mensagem",{})
                                peer_ip = peer_info.get("ip")
                                peer_port = peer_info.get("port")
                                print(f"Iniciando a conversa com {user} em {peer_ip}:{peer_port}")
                                print(f"Digite a sua mensagem para falar com {user}:")
                                texto = input("Digite sua mensagem:")
                                send_message_to_peer(peer_ip, peer_port, usuario_logado, user, texto)
                                #Escrevendo a mensagem em JSON

                                registro_mensagem = {
                                    "usuario_remetente":usuario_logado,
                                    "usuario_destino": user,
                                    "mensagem":texto
                                }
                                msgPath = "messages_list.json"

                                #Verifica se o arquivo já existe e carrega o interior dele
                                if os.path.exists(msgPath):
                                    print("Arquivo existe!")
                                    f = open(msgPath,"r",encoding="utf-8")
                                    recorded_messages = json.load(f)
                                else:
                                    recorded_messages = []
                                recorded_messages.append(registro_mensagem)
                                f = open(msgPath,"w",encoding="utf-8")
                                json.dump(recorded_messages,f,indent=4,ensure_ascii=False)
                            else:
                                print("Erro ao obter infos do User")
                            break
                    print("Este usuário não está online ou não existe!")
                
                input("Pressione Enter para continuar")
                os.system('cls||clear')
            except:
                #print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")
        elif operation == "7":
            dados = {
                "action": "exit",
                "username": usuario_logado
            }
            send_to_tracker(dados)
            usuario_logado = None
            print("sessão finalizada.")
            input("Pressione Enter para continuar.")
            os.system('cls||clear')
            return False
        elif operation == "8":
            announce_files(usuario_logado)
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "9":
            arquivos = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py')]
            try:
                dados = register_chunks(arquivos,usuario_logado)
                send_to_tracker(dados)
            except:
                print("não foi possivel registrar os chunks")
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "10":
            arquivos = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py')]
            try:
                
                dados = pedir_chunks(arquivos,usuario_logado)
                send_to_tracker(dados)
            except:
                print("não foi possivel registrar os chunks")
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        else:
            print("Opção inválida.")
            input("Pressione Enter para continuar")
            os.system('cls||clear')


while True:
    print('Bem vindo ao WhatsApp#2!')
    print('Gostaria de Iniciar o Tracker?\n 1- Sim, 0 - Não')

    ans = int(input())
    if ans == 1:
        if is_tracker_running():
            print("Tracker já está rodando.")
        else:
            print("Não está rodando ainda")
            launch_tracker_cross_platform()
            print("Tracker Inicializado!")

        print("=====BEM VINDO======\nAO WHATSAPP#2")
        result = interactiveMenu_1()
        if result:
            print("Continue!")
            a = int(input())
        else:
            print("End of Program")
            break
    else:
        os.system('cls||clear')
        print("Gostaria de se comportar como um cliente?\n")
        ans2 = int(input(" 1- Sim, 0 - Não\n"))
        if (ans2==1):
            #print("Implementar verificação de existência de Tracker Aitvo!")
            print("=====BEM VINDO======\nAO WHATSAPP#2")
            result = interactiveMenu_1()
            if(result):
                print("Continue!")
                a = int(input())
            else:
                print("End of Program")
                break
        os.system('cls||clear')