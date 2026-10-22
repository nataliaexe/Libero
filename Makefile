.PHONY: help setup venv install run-capture run-vad run-transcribe run-agent test clean deploy

help:
	@echo "Libero - Comandos disponíveis:"
	@echo "  make setup         - Configura o ambiente"
	@echo "  make venv          - Cria o virtualenv"
	@echo "  make install       - Instala dependências"
	@echo "  make run-capture   - Roda captura de áudio"
	@echo "  make run-vad       - Roda detecção de voz"
	@echo "  make run-transcribe- Roda transcrição"
	@echo "  make run-agent     - Roda agente de companhia"
	@echo "  make test          - Roda testes"
	@echo "  make clean         - Limpa arquivos temporários"
	@echo "  make deploy        - Deploy na AWS"

setup:
	sudo apt update
	sudo apt install -y python3 python3-pip python3-venv git curl wget tmux
	@echo "Ambiente configurado."

venv:
	python3 -m venv venv
	@echo "Virtualenv criado. Ative com: source venv/bin/activate"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

run-capture:
	python edge/capture/audio.py

run-vad:
	python edge/capture/vad.py

run-transcribe:
	python edge/processing/transcribe.py

run-agent:
	python cloud/agents/companion.py

test:
	pytest tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f *.wav *.mp3

deploy:
	cd infra/cdk && cdk deploy --all
