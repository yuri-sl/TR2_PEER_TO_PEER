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
menu_2 = "\n4 - Anunciar um Arquivo;\n5 - Listagem de Peers Ativos;\n6 - Iniciar Chat com Peer;\n7 - Montar arquivo;\n8 - Anunciar arquivos manualmente;\n9 - Anunciar todos os chunks;\n10 - Sair do Sistema;"


def launch_tracker_cross_platform() -> None:
    """
    Executa o script 'tracker.py' em um novo terminal, de forma compatível com múltiplos sistemas operacionais.

    - No Windows: abre o 'cmd' com o script sendo executado via 'python'.
    - No Linux: tenta abrir um novo terminal com o script usando 'gnome-terminal', 'xterm' ou 'konsole'. 
      Caso nenhum desses terminais esteja disponível, executa o script diretamente em segundo plano.
    
    A saída de erro padrão é redirecionada para /dev/null (ignorada) em sistemas Linux.
    """
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

def send_to_tracker(data) -> dict:
    """
    Envia dados codificados em JSON para o tracker via socket TCP e aguarda uma resposta.

    Conecta-se ao tracker localizado em 'localhost' na porta 5000. Os dados enviados devem ser serializáveis em JSON.

    Após o envio completo, a função aguarda a resposta do tracker, que também deve estar em formato JSON.

    Retorna:
        dict: A resposta decodificada do tracker, convertida de JSON para dicionário Python.

    Em caso de falha de conexão (por exemplo, se o tracker não estiver em execução),
    imprime uma mensagem de erro e retorna um dicionário indicando a falha.

    Exemplo de retorno em caso de erro:
        {"status": "erro", "mensagem": "Tracker não disponível."}
    """
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
    
def start_heartbeat(username) -> None:
    """
    Inicia uma thread em segundo plano que envia um sinal de "heartbeat" periódico ao tracker.

    Após um breve atraso inicial (1 segundo), a thread envia continuamente uma requisição
    contendo o nome de usuário ao tracker para indicar que o cliente ainda está ativo.

    - Se o tracker responder com algo diferente de {"status": "ok"}, o cliente assume que foi desconectado por inatividade.
    - Em caso de falha de conexão ou resposta inválida, o cliente é encerrado imediatamente.

    O intervalo entre os heartbeats está configurado para 60 segundos.

    Parâmetros:
        username (str): Nome de usuário que será incluído nas mensagens de heartbeat.
    """
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

def salvar_mensagem(usuario_remetente,destinatario,mensagem,caminho_arquivo = "messages_list.json") -> None:
    """
    Salva uma mensagem em um arquivo JSON contendo uma lista de mensagens.

    Cada mensagem é armazenada como um dicionário com os campos:
    - "usuario_remetente": remetente da mensagem,
    - "usuario_destinatario": destinatário da mensagem,
    - "mensagem": o conteúdo da mensagem.

    Caso o arquivo JSON já exista, a função carrega a lista atual de mensagens e adiciona a nova mensagem.
    Se o arquivo não existir, estiver vazio ou apresentar erro de formato, cria uma nova lista.

    Parâmetros:
        usuario_remetente (str): Nome do usuário que envia a mensagem.
        destinatario (str): Nome do usuário destinatário da mensagem.
        mensagem (str): Conteúdo da mensagem a ser salva.
        caminho_arquivo (str, opcional): Caminho do arquivo JSON onde as mensagens serão salvas. Padrão é "messages_list.json".

    Observações:
        - Se o arquivo apresentar conteúdo inválido, ele será sobrescrito com uma nova lista contendo a mensagem atual.
    """
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

    #f = open(caminho_arquivo,"w",encoding="utf-8")
    #json.dumps(mensagens_salvas,f,indent=4,ensure_ascii=False)

        

def is_tracker_running(host = 'localhost',port=5000) -> bool:
    """
    Verifica se o tracker está ativo e aceitando conexões na máquina e porta especificadas.

    Tenta abrir uma conexão TCP com o host e porta indicados.
    Se conseguir conectar, assume que o tracker está rodando e retorna True.
    Se a conexão for recusada, retorna False.

    Parâmetros:
        host (str): Endereço do servidor tracker (padrão 'localhost').
        port (int): Porta TCP do servidor tracker (padrão 5000).

    Retorna:
        bool: True se o tracker está rodando, False caso contrário.
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((host,port))
        s.close()
        return True
    except ConnectionRefusedError:
        return False

def interactiveMenu_1() -> bool:
    """
    Menu para o usuário
    """
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
            arquivos = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.txt')]
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
            #Montar Aquivo
            # Caminho da pasta com os chunks
            pasta_chunks = "chunkscriados"

            # Lista para guardar nomes únicos dos arquivos originais
            nomes_unicos = set()
            if os.path.isdir(pasta_chunks):
                # Percorre todos os arquivos da pasta
                for nome_arquivo in os.listdir(pasta_chunks):
                    if '.' in nome_arquivo:
                        nome_base = nome_arquivo.split('.')[0]  # pega antes do .index
                        nomes_unicos.add(nome_base)

            # Converte para lista se quiser usar como menu
            lista_arquivos = list(nomes_unicos)
            print("Arquivos disponíveis:")
            for i, nome in enumerate(lista_arquivos, start=1):
                print(f"[{i}] - {nome}")

            try:
                arquivo = int(input("Qual arquivo você quer juntar? "))
                arquivo -=1
                dados = {
                    "action": "reassembly",
                    "username": usuario_logado,
                    "arquivo" : lista_arquivos[arquivo]
                }
                resposta = send_to_tracker(dados)
                print(resposta)
                cstracker = resposta["checksum"]
                print(cstracker)
                cs = assemble_file(lista_arquivos[arquivo])
                print(cs)
                if cstracker == cs:
                    print(f"Arquivo reassemblado com sucesso")
                else:
                    raise Exception("Checksum não confere")
            except:
                print("não foi possivel juntar este arquivo por não existir ou nao estar completo")
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "8":
            #8 - Anunciar arquivos manualmente
            announce_file_novo(usuario_logado,"testeAnuncio.txt")
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "9":
            #Anunciar todos os chunks
            arquivos = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.txt')]
            print(arquivos)
            try:
                dados = register_chunks(arquivos,usuario_logado)
                dadosarq = register_arquivos(arquivos,usuario_logado)
                resposta = send_to_tracker(dados)
                print(resposta["mensagem"])
                resposta = send_to_tracker(dadosarq)
                print(resposta["mensagem"])
            except:
                print("não foi possivel registrar os chunks")
            input("Pressione Enter para continuar")
            os.system('cls||clear')
        elif operation == "10":
            #Sair do sistema
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
        else:
            print("Opção inválida.")
            input("Pressione Enter para continuar")
            os.system('cls||clear')


def init():
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

if __name__ == "__main__":
    init()