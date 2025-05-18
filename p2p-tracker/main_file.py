from tracker import *
import subprocess
import sys
import os
import socket
import json
import random
from peer_messages import *

menu_1 = "MENU PRINCIPAL \n1 - Registrar;\n2 - Login no Sistema;\n3 - Sair do sistema;"
menu_2 = "\n4 - Anunciar um Arquivo;\n5 - Listagem de Peers Ativos;\n6 - Iniciar Chat com Peer \n7- Sair do Sistema;"

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
        #response = s.recv(4096)
        return json.loads(buffer.decode())
    except ConnectionRefusedError:
        print("Não foi possível iniciar o Tracker. ele já está ativo?")
        return {"status":"erro","mensagem":"Tracker não disponível."}

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
    chat_host = 'localhost'

    while True:
        os.system('cls||clear')
        print(menu_1)
        operation = int(input("insira a sua operação desejada:\n"))

        if operation == 1:
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

        elif operation == 2:
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
            print("Dados recebidos!")
            print(resposta)

            if resposta.get("status") == "ok":
                print(resposta["mensagem"])
                usuario_logado = username_login
                start_peer_server(chat_port,usuario_logado)
                break  # break the first menu loop and go to the second
            input("Pressione enter para continuar")

        elif operation == 3:
            print("Bye Bye!!")
            exit()
            return False
        else:
            print("Operação inválida!")
            input("Pressione Enter para continuar")

    # Now you're logged in (usuario_logado is set)
    while usuario_logado:
        os.system('cls||clear')
        print(menu_2)
        operation = int(input("insira a sua operação desejada:\n"))

        if operation == 4:
            try:
                dados = {
                    "action": "list_files",
                    "username": usuario_logado
                }
                resposta = send_to_tracker(dados)
                print("Arquivos dos Peers Ativos: ")
                print(files)
                input("Pressione Enter para continuar")
            except:
                print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")

        elif operation == 5:
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
            except:
                print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")
        elif operation == 6:
            try:
                dados = {
                    "action": "list_clients",
                    "username": usuario_logado
                }
                resposta = send_to_tracker(dados)
                print("Peers Ativos: ")
                for peer in resposta.get("mensagem", []):
                    print(f" - {peer}")
                accept_chat = int(input(("Gostaria de comunicar com um Peer?\n1-Sim    0-Não\n")))
                if accept_chat == 1:
                    selected_user = (input("Digite o nome do usuário que deseja falar com"))
                    for user in resposta.get("mensagem",[]):
                        if selected_user == user:
                            print("Usuário Escolhido para conversar com sucesso!")
                            dados_start_chat = {
                                "action":"get_peer_info",
                                "username":selected_user
                            }
                            resposta_start_chat = send_to_tracker(dados_start_chat)

                            if resposta_start_chat.get("status")=="ok":
                                peer_info = resposta_start_chat.get("mensagem",{})
                                peer_ip = peer_info.get("ip")
                                peer_port = peer_info.get("port")
                                print(f"Iniciando a conversa com {selected_user} em {peer_ip}:{peer_port}")
                                print(f"Digite a sua mensagem para falar com {selected_user}:")
                                texto = input("Digite sua mensagem:")
                                send_message_to_peer(peer_ip,peer_port,usuario_logado,selected_user,texto)
                            else:
                                print("Erro ao obter infos do User")
                            break


                        else:
                            print("Este usuário não está online ou não existe!")

                input("Pressione Enter para continuar")
            except:
                print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")
        elif operation == 7:
            dados = {
                "action": "exit",
                "username": usuario_logado
            }
            send_to_tracker(dados)
            usuario_logado = None
            print("sessão finalizada.")
            input("Pressione Enter para continuar.")
            return False
        else:
            print("Opção inválida.")
            input("Pressione Enter para continuar")


while True:
    print('Bem vindo ao WhatsApp#2!')
    print('Gostaria de Iniciar o Tracker?\n 1- Sim, 0 - Não')

    ans = int(input())
    if (ans==1):
        if is_tracker_running():
            print("Tracker já está rodando.")
        subprocess.Popen(['start', 'cmd', '/k', f'python tracker.py'], shell=True)
        #start_tracker()
        print("Tracker Inicializado!")
        print("=====BEM VINDO======\nAO WHATSAPP#2")
        result = interactiveMenu_1()
        if(result):
            print("Continue!")
            a = int(input())
        else:
            print("End of Program")
            break
    else:
        print("Gostaria de se comportar como um cliente?")
        ans2 = int(input(" 1- Sim, 0 - Não"))
        if (ans2==1):
            print("Implementar verificação de existência de Tracker Aivo!")
            print("=====BEM VINDO======\nAO WHATSAPP#2")
            result = interactiveMenu_1()
            if(result):
                print("Continue!")
                a = int(input())
            else:
                print("End of Program")
                break