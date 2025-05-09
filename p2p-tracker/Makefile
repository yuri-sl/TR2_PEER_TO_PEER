# Nome do arquivo: Makefile

server:				# rodar primeiro em um bash
	python3 tracker.py

client:				# rodar depois em um outro bash
	python3 cliente_teste_register.py
	python3 cliente_teste_login.py
	python3 cliente_teste_peers.py

kill:					# finalizar o teste
	pkill -f tracker.py
	