import matplotlib.pyplot as plt
import json



#VolumeDeDados
with open("scoreboard.json") as f:
    data = json.load(f)

peers = data.keys()
volumes = [data[p]["bytes_sent"] for p in peers]

plt.bar(peers, volumes)
plt.xlabel("Peers")
plt.ylabel("Bytes Enviados")
plt.show()

#Ex2: Histograma de tempos de transferência
all_times = []
for p in data:
    all_times.extend(data[p].get("transfer_times", []))

plt.hist(all_times, bins=10)
plt.xlabel("Tempo de transferência (s)")
plt.ylabel("Frequência")
plt.show()


#Sucesso vs Falha
success_count = sum(data[p].get("successful_responses", 0) for p in data)
fail_count = sum(data[p].get("failed_transfers", 0) for p in data)

plt.pie([success_count, fail_count], labels=["Sucesso", "Falha"], autopct='%1.1f%%')
plt.show()
