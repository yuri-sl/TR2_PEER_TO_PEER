from tracker import *
import subprocess
import sys
import os
import socket
import json

menu_1 = "MENU PRINCIPAL \n1 - Registrar;\n2 - Login no Sistema;\n3 - Sair do sistema;"
menu_2 = "\n4 - Anunciar um Arquivo;\n5 - Listagem de Peers Ativos;\n6 - Sair do sistema;"

def send_to_tracker(data):
    HOST = 'localhost'
    PORT = 5000
    try:    
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((HOST,PORT))
        s.sendall(json.dumps(data).encode())
        s.shutdown(socket.SHUT_WR)  # Indica que terminou de enviar dados
        response = s.recv(4096)
        return json.loads(response.decode())
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
            dados = {
                "action": "login",
                "username": username_login,
                "password": password
            }
            resposta = send_to_tracker(dados)
            print("Dados recebidos!")
            print(resposta)

            if resposta.get("status") == "ok":
                print(resposta["mensagem"])
                usuario_logado = username_login
                break  # break the first menu loop and go to the second
            input("Pressione enter para continuar")

        elif operation == 3:
            print("Bye Bye!!")
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
                for files in resposta.get("mensagem", []):
                    print(f" - {files}")
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
                    print(f" - {peer}")
                input("Pressione Enter para continuar")
            except:
                print("Você provavavelmente foi desligado por inatividade")
                input("Pressione Enter para continuar")

        elif operation == 6:
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
        ans2 = int(input("1- Sim\n\t0 - Não"))
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