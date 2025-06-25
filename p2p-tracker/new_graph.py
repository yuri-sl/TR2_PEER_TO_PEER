import json
import matplotlib.pyplot as plt

# Carrega o JSON
with open('transfer_metrics.json', 'r') as f:
    data = json.load(f)

# Extrai tempos e volumes
a_tempos = [item["tempo"] for item in data["A"]]
f_tempos = [item["tempo"] for item in data["F"]]

a_volumes = [item["volume"] for item in data["A"]]
f_volumes = [item["volume"] for item in data["F"]]

# ---- Plot dos tempos ----
plt.figure(figsize=(10, 5))
plt.plot(range(len(a_tempos)), a_tempos, 'o-', label='A - Tempo')
plt.plot(range(len(f_tempos)), f_tempos, 'x-', label='F - Tempo')
plt.title('Tempos dos Chunks (A e F)')
plt.xlabel('Índice do chunk')
plt.ylabel('Tempo (s)')
plt.legend()
plt.grid(True)
plt.show()

# ---- Plot dos volumes ----
plt.figure(figsize=(10, 5))
plt.plot(range(len(a_volumes)), a_volumes, 'o-', label='A - Volume')
plt.plot(range(len(f_volumes)), f_volumes, 'x-', label='F - Volume')
plt.title('Volumes dos Chunks (A e F)')
plt.xlabel('Índice do chunk')
plt.ylabel('Volume')
plt.legend()
plt.grid(True)
plt.show()
