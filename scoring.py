import json
import os
import time
import math

# Caminho para salvar o scoreboard
SCOREBOARD_FILE = "scoreboard.json"

# Scoreboard global em memória
scoreboard = {}


def map_score_to_range(score: float) -> int:
    """
    Mapeia um score qualquer para o intervalo fixo de 0 a 100 em incrementos de 10.
    Arredonda para o múltiplo de 10 mais próximo, sem ultrapassar 100.

    Args:
        score (float): Score bruto calculado.

    Returns:
        int: Score normalizado de 0 a 100 em passos de 10.
    """
    if score <= 0:
        return 0
    elif score >= 100:
        return 100
    else:
        return min(100, round(score / 10) * 10)

# Pesos configuráveis para cada métrica
WEIGHTS = {
    'bytes_sent': 0.001,
    'time_connected': 1,
    'successful_responses': 1,
    'active_connections':1,
    "failed_transfers" : -1

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
        except (json.JSONDecodeError, IOError) as e:
            #print(f"Erro ao carregar o scoreboard ({e}). Inicializando vazio.")
            scoreboard = {}  # Nesse caso, só resetamos quando não dá pra ler.
    else:
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

    if score >= 80:
        return {"prioridade": "alta", "max_conexoes": 4, "largura_banda": 16384}
    elif score > 30:
        return {"prioridade": "media", "max_conexoes": 2, "largura_banda": 8192}
    else:
        return {"prioridade": "baixa", "max_conexoes": 1, "largura_banda": 4096}

def update_score(peer_id: str, bytes_sent: int = 0, time_connected: int = 0,
                 successful_responses: int = 0, failed_transfers: int = 0,
                 transfer_time: float = None, integrity_check: bool = None,
                 active_connections: int = 0, log_history=False) -> int:
    """Atualiza todas as métricas para o peer."""

    global scoreboard

    #scoreboard = load_scoreboard()
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
    metrics["active_connections"] = active_connections


    if integrity_check is not None:
        chunk_name = f"chunk_{int(time.time())}"
        metrics["integrity_checks"][chunk_name] = integrity_check

    # Recalcula score
    if metrics["time_connected"] <= 60:
        score = (
            WEIGHTS.get("bytes_sent", 0.05) * math.log1p(metrics["bytes_sent"]) +
            WEIGHTS.get("time_connected", 1) * metrics["time_connected"] +
            WEIGHTS.get("successful_responses", 1) * metrics["successful_responses"] +
            WEIGHTS.get("failed_transfers", -1) * metrics["failed_transfers"] +
            WEIGHTS.get("active_connections", 1) * metrics["active_connections"]
        )
    else:
        score = (
            WEIGHTS.get("bytes_sent", 0.05) * math.log1p(metrics["bytes_sent"]) +
            30 + # sempre vale 30 pontos caso tenha mais que 60 segundos no serivdor
            WEIGHTS.get("successful_responses", 1) * metrics["successful_responses"] + 
            WEIGHTS.get("failed_transfers", -1) * metrics["failed_transfers"] +
            WEIGHTS.get("active_connections", 1) * metrics["active_connections"]
        )
    #metrics["score"] = map_score_to_range(score)
    score = min(score,1000)

    metrics["score"] = score
    scoreboard[peer_id] = metrics
    save_scoreboard()
    return metrics["score"]

# Carrega o scoreboard ao iniciar o programa
load_scoreboard()


#score_example = update_score("peerA", bytes_sent=1000, time_connected=2.0, successful_responses=1)
#save_scoreboard()
#print(f"Nova pontuação de peerA: {score_example}")

def get_score(peer_id: str, normalize=False) -> int:
    """
    Retorna a pontuação atual de um peer.

    Args:
        peer_id (str): ID do peer.
        normalize (bool): Se True, retorna score entre 0 e 100.

    Returns:
        int: Score do peer.
    """
    global scoreboard
    load_scoreboard()

    metrics = scoreboard.get(peer_id)
    if metrics and isinstance(metrics, dict):
        raw_score = metrics.get("score", 0)
        if normalize:
            return min(100, int(raw_score / 10))
        return raw_score
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