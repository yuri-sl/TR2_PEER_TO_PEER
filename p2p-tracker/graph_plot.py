import json
import matplotlib.pyplot as plt
import statistics

# Carrega o scoreboard atual
with open("scoreboard.json") as f:
    data = json.load(f)

# ---- Gráfico 1: Volume de dados enviados ----
peers = data.keys()
volumes = [data[p]["bytes_sent"] for p in peers]

plt.figure(figsize=(10,5))
plt.bar(peers, volumes, color="royalblue")
plt.ylabel("Bytes Enviados")
plt.xlabel("Peers")
plt.title("Volume de dados enviados por Peer")
plt.show()

# ---- Gráfico 2: Sucesso vs. Falha ----
successes = sum(data[p]["successful_responses"] for p in data)
fails = sum(data[p]["failed_transfers"] for p in data)

plt.figure(figsize=(5,5))
plt.pie([successes, fails], labels=["Sucessos", "Falhas"], autopct="%1.1f%%", startangle=90)
plt.title("Taxa de Sucesso vs. Falha nas Transferências")
plt.show()

# ---- Gráfico 3: Histograma dos tempos de transferência ----
all_times = []
for p in data:
    all_times.extend(data[p]["transfer_times"])

plt.figure(figsize=(10,5))
plt.hist(all_times, bins=10, color="green", edgecolor="black")
plt.xlabel("Tempo de transferência (s)")
plt.ylabel("Frequência")
plt.title("Distribuição dos tempos de transferência")
plt.show()

# ---- Gráfico 4: Verificação de integridade ----
correct_count = 0
incorrect_count = 0
for p in data:
    for result in data[p]["integrity_checks"].values():
        if result:
            correct_count += 1
        else:
            incorrect_count += 1

plt.figure(figsize=(5,5))
plt.pie([correct_count, incorrect_count],
        labels=["Integridade Confirmada", "Integridade Falha"],
        autopct="%1.1f%%",
        startangle=90,
        colors=["green", "red"])
plt.title("Resultado das Verificações de Integridade")
plt.show()
