# Nome do arquivo: Makefile

server:				# rodar primeiro em um bash
	python3 tracker.py

client:				# rodar depois em um outro bash
#	Este já ira estar cadastrado
	python3 cliente_teste_register.py
#	Este vai cadastrar ainda			
	python3 cliente_teste_register2.py
	sleep 2
#	Logar os dois para testar login e threading e heartbeat
	python3 cliente_teste_login.py
	python3 cliente_teste_login2.py
	sleep 3
#	Ver os peers ativos e reinicio do heartbeat
	python3 cliente_teste_peers.py
	python3 cliente_teste_exit.py

kill:					# finalizar o teste
	pkill -f tracker.py
	