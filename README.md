# TR2_PEER_TO_PEER

Para testar o projeto que implementa um **Tracker** e é responsável por gerenciar e autenticar os **peers**, registrar arquivos e manter uma lista dos **peers** ativos.

## 🚀 Como Testar

### 1. Inicie o Tracker:
Abra um terminal e execute o comando abaixo para rodar o servidor **Tracker**:
```bash
make server
### 2. Inicie os testes do cliente:
Abra um outro terminal e execute o comando abaixo para rodar o **cliente**:
```bash
make client
### 3. Finalize o tracker:
No mesmo terminal do cliente execute o comando abaixo:
```bash
make kill