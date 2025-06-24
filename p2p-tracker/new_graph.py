import json
import matplotlib.pyplot as plt

SCOREBOARD_FILE = "transfer_metrics.json"  # ajuste para seu arquivo atual

def load_scoreboard():
    with open(SCOREBOARD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def plot_metrics(user):
    data = load_scoreboard()
    if user not in data:
        print(f"Usuário {user} não encontrado.")
        return

    user_data = data[user]

    # O primeiro elemento não parece ser uma métrica temporal, pulamos
    metrics = user_data[1:]  # Pega só os dicts com tempo, volume e integridade

    tempos = [entry["tempo"] for entry in metrics]
    volumes = [entry["volume"] for entry in metrics]
    integridades = [entry["integridade"] for entry in metrics]

    # Plota o volume ao longo do tempo
    plt.figure(figsize=(12, 6))
    plt.plot(tempos, volumes, label="Volume", marker="o")

    # Se quiser indicar integridade com cores diferentes:
    for t, v, i in zip(tempos, volumes, integridades):
        color = "green" if i else "red"
        plt.scatter(t, v, color=color, s=100)

    plt.xlabel("Tempo (segundos?)")
    plt.ylabel("Volume")
    plt.title(f"Métricas do usuário {user}")
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    user_to_plot = input("Digite o nome do usuário para visualizar o gráfico: ")
    plot_metrics(user_to_plot)
