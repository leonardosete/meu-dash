# Makefile para automação de tarefas comuns no projeto meu-dash

# Define o interpretador Python a ser usado. Procura por um ambiente virtual.
PYTHON := $(shell if [ -d ".venv" ]; then echo ".venv/bin/python"; else echo "python3"; fi)

# Define o nome da imagem Docker e a tag.
DOCKER_IMAGE_NAME := meu-dash
DOCKER_IMAGE_TAG := latest

.PHONY: help install setup run test format lint check clean docker-build docker-run

help:
	@echo "Comandos disponíveis:"
	@echo "  make install        - Instala as dependências do requirements.txt."
	@echo "  make setup          - Cria o ambiente virtual e instala as dependências."
	@echo "  make run            - Inicia a aplicação Flask em modo de desenvolvimento."
	@echo "  make migrate        - Aplica as migrações do banco de dados (cria as tabelas)."
	@echo "  make test           - Executa a suíte de testes com pytest."
	@echo "  make format         - Formata o código com 'black'."
	@echo "  make lint           - Executa o linter 'ruff check --fix' para corrigir erros."
	@echo "  make check          - Roda o formatador e o linter em modo de verificação (para CI)."
	@echo "  make clean          - Remove arquivos temporários e caches."
	@echo "  make docker-build   - Constrói a imagem Docker da aplicação."
	@echo "  make docker-run     - Executa a aplicação a partir da imagem Docker."

setup:
	@echo ">>> Configurando ambiente virtual em .venv..."
	python3 -m venv .venv
	@$(PYTHON) -m pip install --upgrade pip
	@make install

install:
	@echo ">>> Instalando dependências de requirements.txt..."
	@$(PYTHON) -m pip install -r requirements.txt

run:
	@echo ">>> Iniciando a aplicação em modo de desenvolvimento..."
	@export PYTHONPATH=$(shell pwd) && \
	export FLASK_APP=src.app && \
	export FLASK_DEBUG=True && \
	.venv/bin/flask run

test:
	@echo ">>> Executando testes com pytest..."
	@export PYTHONPATH=$(shell pwd) && \
	.venv/bin/pytest

migrate:
	@echo ">>> Aplicando migrações do banco de dados..."
	@export PYTHONPATH=$(shell pwd) && \
	export FLASK_APP=src.app && \
	.venv/bin/flask db upgrade

format:
	@echo ">>> Formatando o código com black..."
	@.venv/bin/black .

lint:
	@echo ">>> Executando linter com ruff check..."
	@.venv/bin/ruff check --fix .

check:
	@echo ">>> Verificando formatação com black..."
	@.venv/bin/black --check .
	@echo ">>> Verificando código com ruff check..."
	@.venv/bin/ruff check .

clean:
	@echo ">>> Removendo caches e arquivos temporários..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -f .coverage

docker-build:
	@echo ">>> Construindo imagem Docker: $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)..."
	@docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) .

docker-run:
	@echo ">>> Executando container Docker..."
	@docker run -p 5000:5000 -v $(shell pwd)/data:/app/data $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
