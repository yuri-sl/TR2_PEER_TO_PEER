from tracker import *
import subprocess
import sys
import os

menu_1 = "MENU PRINCIPAL \n1 - Registrar;\n2 - Login no Sistema;\n3 - Sair do sistema;"
menu_2 = "\n4 - Anunciar um Arquivo;\n5 - Listagem de Peers Ativos;\n6 - Sair do sistema;"

def interactiveMenu_1():
    while(True):
        os.system('cls||clear')
        print(menu_1)   
        operation = int(input("insira a sua operação desejada:\n")) 
        if(operation==1):
            usernameRegister = input("Defina seu nome de usuário: ")
            passwordRegister = input("Defina a sua senha: ")
            confirm_password = input("Confirme a sua senha:")

            print("Usuário criado com sucesso!")
        elif(operation==2):
            username_login = input("Insira o seu nome de usuário")
            password = input("Insira sua senha:")
        elif(operation==3):
            print("Bye Bye!!")
            return False

while True:
    print('Bem vindo ao WhatsApp#2!')
    print('Gostaria de Iniciar o Tracker?\n 1- Sim, 0 - Não')

    ans = int(input())
    if (ans==1):
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
        print("Encerrando a execução!")
        break