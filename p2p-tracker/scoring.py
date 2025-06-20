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
        with open(SCOREBOARD_FILE, "r", encoding="utf-8") as f:
            scoreboard = json.load(f)

# Pesos configuráveis para cada métrica
WEIGHTS = {
    'bytes_sent': 0.5,
    'time_connected': 0.3,
    'successful_responses': 0.2
}


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

    Side Effects:
        - Atualiza `scoreboard[peer_id]` com a nova pontuação.
    """
    # Normalização simples (pode ser aprimorada)
    score = (
        WEIGHTS['bytes_sent'] * bytes_sent +
        WEIGHTS['time_connected'] * time_connected +
        WEIGHTS['successful_responses'] * successful_responses
    )
    scoreboard[peer_id] = score
    return score

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