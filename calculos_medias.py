import json
import statistics

def calcular_estatisticas_arquivo(caminho_arquivo):
    """
    Lê o arquivo JSON de métricas de transferência e retorna
    a média e o desvio padrão dos tempos para cada usuário.

    Parâmetros:
        caminho_arquivo (str): Caminho para o arquivo JSON.

    Retorna:
        dict: Resultado no formato:
            {
              "Usuario": {"media": float, "desvio_padrao": float},
              ...
            }
    """
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        dados = json.load(f)

    resultado = {}
    for usuario, registros in dados.items():
        tempos = [item["tempo"] for item in registros if "tempo" in item]
        media = statistics.mean(tempos) if tempos else 0.0
        desvio = statistics.stdev(tempos) if len(tempos) > 1 else 0.0
        resultado[usuario] = {"media": media, "desvio_padrao": desvio}
    return resultado


# Exemplo de uso:
caminho = "transfer_metrics_single.json"
estatisticas = calcular_estatisticas_arquivo(caminho)

# Resultado
print(json.dumps(estatisticas, indent=4))
