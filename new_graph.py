import json
import matplotlib.pyplot as plt
import json
import matplotlib.pyplot as plt

import json
import matplotlib.pyplot as plt

def plotarGraficoSingle():
    # Carrega o JSON
    with open('transfer_metrics_single.json', 'r') as f:
        data = json.load(f)

    # Extrai tempos e volumes
    a_tempos = [item["tempo"] for item in data.get("A", [])]
    f_tempos = [item["tempo"] for item in data.get("F", [])]
    c_tempos = [item["tempo"] for item in data.get("c", [])]

    a_volumes = [item["volume"] for item in data.get("A", [])]
    f_volumes = [item["volume"] for item in data.get("F", [])]
    c_volumes = [item["volume"] for item in data.get("c", [])]

    # ---- Gráfico de Linha Volume vs Tempo ----
    plt.figure(figsize=(10, 5))
    plt.plot(a_tempos, a_volumes, 'o-', label='Baixados por A')
    plt.plot(f_tempos, f_volumes, 'x-', label='Baixados por F')
    plt.plot(c_tempos, c_volumes, '^-', label='Baixados por c')
    plt.title('Volume vs Tempo para A, F e c')
    plt.xlabel('Tempo (s)')
    plt.ylabel('Volume (bytes)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()



def plotarGraficoMultiplas():
    # Carrega o JSON
    with open('transfer_metrics_connections.json', 'r') as f:
        data = json.load(f)

    # Extrai tempos e volumes
    a_tempos = [item["tempo"] for item in data["A"]]
    f_tempos = [item["tempo"] for item in data["F"]]
    c_tempos = [item["tempo"] for item in data["c"]]

    a_volumes = [item["volume"] for item in data["A"]]
    f_volumes = [item["volume"] for item in data["F"]]
    c_volumes = [item["volume"] for item in data["c"]]
    # ---- Plot Volume vs Tempo ----
    # ---- Plot Volume vs Tempo ----
    plt.figure(figsize=(10, 5))
    plt.plot(a_tempos, a_volumes, 'o-', label='A (volume vs tempo)')
    plt.plot(f_tempos, f_volumes, 'x-', label='F (volume vs tempo)')
    plt.plot(c_tempos,c_volumes,'x-',label='Baixados por c (volume vs tempo)')
    plt.title('Volume vs Tempo para A, F e c')
    plt.xlabel('Tempo (s)')
    plt.ylabel('Volume')
    plt.legend()
    plt.grid(True)
    plt.show()
