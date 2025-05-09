import socket
import json
import os

HOST = 'localhost'
PORT = 5000
USER_LIST_PATH = 'user_list.json'

mensagem = {
    "action": "login",
    "username": "shinigami2",
    "password": "123456"
}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall(json.dumps(mensagem).encode())
s.shutdown(socket.SHUT_WR)  # Indica que terminou de enviar dados
resposta = s.recv(4096)
print("Resposta:", resposta.decode())
"""
print(mensagem['action'] == 'login')
if (mensagem['action'] == 'login'):
    username = mensagem['username']
    password = mensagem['password']
    result = (username,password)


if os.path.exists(USER_LIST_PATH):
    #print("Existe o arquivo!")
    f = open(USER_LIST_PATH, 'r')
    print(json.load(f))
    #return json.load(f)
"""
# def carregar_usuarios():
#     if not os.path.exists(USER_LIST_PATH):
#         open()