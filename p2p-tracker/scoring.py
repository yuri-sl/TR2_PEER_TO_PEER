import json
import os

# Caminho para salvar o scoreboard
SCOREBOARD_FILE = "scoreboard.json"

# Scoreboard global em memória
scoreboard = {}

# Pesos configuráveis para cada métrica
WEIGHTS = {
    'bytes_sent': 0.00000000001,
    'time_connected': 1,
    'successful_responses': 10,
    'active_connections':2
}
conexoes_ativas = {}  # Ex.: {"a": 1, "b": 2, ...}

def threads_ativas_para(username):
    """Retorna quantas threads estão ativadas para o peer especificado."""
    return conexoes_ativas.get(username, 0)

def adicionar_conexao(username):
    """Incrementa contador de conexão para o peer."""
    conexoes_ativas[username] = conexoes_ativas.get(username, 0) + 1

def remover_conexao(username):
    """Decrementa contador de conexão para o peer."""
    conexoes_ativas[username] = max(conexoes_ativas.get(username, 1) - 1, 0)

def load_scoreboard():
    """Carrega o scoreboard do disco se existir."""
    global scoreboard
    if os.path.exists(SCOREBOARD_FILE):
        try:
            with open(SCOREBOARD_FILE, "r", encoding="utf-8") as f:
                scoreboard = json.load(f)
        except (json.JSONDecodeError, IOError):
            print("Erro ao carregar o scoreboard. Inicializando vazio.")
            print(f"O scoreboard é {scoreboard}")
            scoreboard = {}
    return scoreboard

def save_scoreboard():
    """Salva o scoreboard atual no disco."""
    try:
        with open(SCOREBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(scoreboard, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Erro ao salvar o scoreboard: {e}")
def get_peer_priority(username, scoreboard):
    """Retorna prioridade, max_conexões e largura de banda para um peer com base no seu score."""
    dados = scoreboard.get(username, {})
    score = dados.get("score", 0)

    if score > 100000:
        return {"prioridade": "alta", "max_conexoes": 4, "largura_banda": 16384}
    elif score > 50000:
        return {"prioridade": "media", "max_conexoes": 2, "largura_banda": 8192}
    else:
        return {"prioridade": "baixa", "max_conexoes": 1, "largura_banda": 4096}

def update_score(peer_id: str, bytes_sent: int = 0, time_connected: int = 0,
                 successful_responses: int = 0, failed_transfers: int = 0,
                 transfer_time: float = None, integrity_check: bool = None,
                 active_connections: int = 0, log_history=False) -> int:
    """Atualiza todas as métricas para o peer."""

    scoreboard = load_scoreboard()
    metrics = scoreboard.get(peer_id, {
        "bytes_sent": 0,
        "time_connected": 0,
        "successful_responses": 0,
        "failed_transfers": 0,
        "transfer_times": [],
        "integrity_checks": {},
        "active_connections": 0,
        "score": 0
    })

    # Atualiza
    metrics["bytes_sent"] += bytes_sent
    metrics["time_connected"] += time_connected
    metrics["successful_responses"] += successful_responses
    metrics["failed_transfers"] += failed_transfers
    metrics["active_connections"] += active_connections


    if integrity_check is not None:
        chunk_name = f"chunk_{int(time.time())}"
        metrics["integrity_checks"][chunk_name] = integrity_check

    # Recalcula score
    score = (
        WEIGHTS.get("bytes_sent", 1) * metrics["bytes_sent"] +
        WEIGHTS.get("time_connected", 1) * metrics["time_connected"] +
        WEIGHTS.get("successful_responses", 1) * metrics["successful_responses"] +
        WEIGHTS.get("active_connections", 1) * metrics["active_connections"]
    )
    metrics["score"] = score

    scoreboard[peer_id] = metrics
    save_scoreboard()
    return metrics["score"]

# Carrega o scoreboard ao iniciar o programa
load_scoreboard()


#score_example = update_score("peerA", bytes_sent=1000, time_connected=2.0, successful_responses=1)
#save_scoreboard()
#print(f"Nova pontuação de peerA: {score_example}")

def get_score(peer_id: str) -> int:
    """
    Retorna a pontuação atual de um peer.

    Args:
        peer_id (str): Identificador do peer.

    Returns:
        int: Pontuação armazenada, ou 0 se não existir.
    """
    score = load_scoreboard()
    metrics = score.get(peer_id)
    if metrics and isinstance(metrics, dict):
        return metrics.get("score", 0)
    return 0

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