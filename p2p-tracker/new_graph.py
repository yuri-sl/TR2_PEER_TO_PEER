import json
import matplotlib.pyplot as plt

# Carrega o JSON
with open('transfer_metrics_single.json', 'r') as f:
    data = json.load(f)

# Extrai tempos e volumes
a_tempos = [item["tempo"] for item in data["A"]]
f_tempos = [item["tempo"] for item in data["F"]]

a_volumes = [item["volume"] for item in data["A"]]
f_volumes = [item["volume"] for item in data["F"]]

# ---- Plot Volume vs Tempo ----
# ---- Plot Volume vs Tempo ----
plt.figure(figsize=(10, 5))
plt.plot(a_tempos, a_volumes, 'o-', label='A (volume vs tempo)')
plt.plot(f_tempos, f_volumes, 'x-', label='F (volume vs tempo)')
plt.title('Volume vs Tempo para A e F')
plt.xlabel('Tempo (s)')
plt.ylabel('Volume')
plt.legend()
plt.grid(True)
plt.show()

