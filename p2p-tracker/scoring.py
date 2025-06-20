import json
import os

# Caminho para salvar o scoreboard
SCOREBOARD_FILE = "scoreboard.json"

# Scoreboard global em memória
scoreboard = {}

# Pesos configuráveis para cada métrica
WEIGHTS = {
    'bytes_sent': 0.5,
    'time_connected': 0.3,
    'successful_responses': 0.2
}

def load_scoreboard():
    """Carrega o scoreboard do disco se existir."""
    global scoreboard
    if os.path.exists(SCOREBOARD_FILE):
        try:
            with open(SCOREBOARD_FILE, "r", encoding="utf-8") as f:
                scoreboard = json.load(f)
        except (json.JSONDecodeError, IOError):
            print("Erro ao carregar o scoreboard. Inicializando vazio.")
            scoreboard = {}

def save_scoreboard():
    """Salva o scoreboard atual no disco."""
    try:
        with open(SCOREBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(scoreboard, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Erro ao salvar o scoreboard: {e}")

def update_score(peer_id: str, bytes_sent: int, time_connected: float, successful_responses: int) -> float:
    """
    Atualiza a pontuação de um peer com base em métricas de envio.

    Args:
        peer_id (str): Identificador único do peer.
        bytes_sent (int): Total de bytes enviados pelo peer desde último update.
        time_connected (float): Tempo (em segundos) conectado.
        successful_responses (int): Número de respostas de chunk bem-sucedidas.

    Returns:
        float: Nova pontuação calculada para o peer.
    """
    # Recupera métricas anteriores ou inicializa
    metrics = scoreboard.get(peer_id, {
        "bytes_sent": 0,
        "time_connected": 0.0,
        "successful_responses": 0,
        "score": 0.0
    })

    # Atualiza métricas
    metrics["bytes_sent"] += bytes_sent
    metrics["time_connected"] += time_connected
    metrics["successful_responses"] += successful_responses

    # Calcula nova pontuação
    score = (
        WEIGHTS["bytes_sent"] * metrics["bytes_sent"] +
        WEIGHTS["time_connected"] * metrics["time_connected"] +
        WEIGHTS["successful_responses"] * metrics["successful_responses"]
    )

    metrics["score"] = round(score, 2)
    scoreboard[peer_id] = metrics
    save_scoreboard()
    return metrics["score"]

# Carrega o scoreboard ao iniciar o programa
load_scoreboard()


#score_example = update_score("peerA", bytes_sent=1000, time_connected=2.0, successful_responses=1)
#save_scoreboard()
#print(f"Nova pontuação de peerA: {score_example}")

def get_score(peer_id: str) -> float:
    """
    Retorna a pontuação atual de um peer.

    Args:
        peer_id (str): Identificador do peer.

    Returns:
        float: Pontuação armazenada, ou 0.0 se não existir.
    """
    return scoreboard.get(peer_id, 0.0)

def get_leaderboard(top_n: int = None) -> list:
    """
    Retorna a lista de peers ordenados pela pontuação decrescente.

    Args:
        top_n (int, optional): Quantidade de top peers a retornar. Se None, retorna todos.

    Returns:
        list of tuples: [(peer_id, score), ...] ordenado.
    """
    sorted_list = sorted(scoreboard.items(), key=lambda x: x[1], reverse=True)
    return sorted_list[:top_n] if top_n else sorted_list