# Makefile para automação de tarefas comuns no projeto meu-dash

# Define o interpretador Python a ser usado. Procura por um ambiente virtual.
PYTHON := $(shell if [ -d ".venv" ]; then echo ".venv/bin/python"; else echo "python3"; fi)

# Define o nome da imagem Docker e a tag.
DOCKER_IMAGE_NAME := meu-dash
DOCKER_IMAGE_TAG := latest

.PHONY: help install setup run test format lint check clean distclean docker-build docker-run validate

help:
	@echo "Comandos disponíveis:"
	@echo "  make install        - Instala as dependências do requirements.txt."
	@echo "  make setup          - Cria o ambiente virtual e instala as dependências."
	@echo "  make setup-and-run  - (FAZ-TUDO) Configura o ambiente do zero e inicia a aplicação."
	@echo "  make run            - Inicia a aplicação Flask em modo de desenvolvimento."
	@echo "  make fresh-run      - Limpa o DB, aplica migrações e inicia a aplicação (para testes)."
	@echo "  make migrate        - Aplica as migrações do banco de dados."
	@echo "  make test           - Executa a suíte de testes com pytest."
	@echo "  make format         - Formata o código com 'ruff format'."
	@echo "  make lint           - Executa o linter 'ruff check --fix' para corrigir erros."
	@echo "  make security-scan  - Roda a verificação de segurança com 'bandit'."
	@echo "  make check          - Roda todas as verificações: formatação, linting e segurança (para CI)."
	@echo "  make validate       - (TUDO-EM-UM) Instala dependências, formata e testa o projeto."
	@echo "  make clean          - Remove arquivos temporários e caches."
	@echo "  make distclean      - Remove TODOS os arquivos gerados (venv, db, relatórios)."
	@echo "  make docker-build   - Constrói a imagem Docker da aplicação."
	@echo "  make docker-run     - Executa a aplicação a partir da imagem Docker."

# Cria o ambiente virtual e instala as dependências nele.
setup:
	@echo ">>> Configurando ambiente virtual em .venv..."
	@python3 -m venv .venv
	@echo ">>> Atualizando pip e instalando dependências no ambiente virtual..."
	@.venv/bin/pip install --upgrade pip -r requirements.txt

install:
	@echo ">>> Instalando dependências de requirements.txt..."
	@$(PYTHON) -m pip install -r requirements.txt

setup-and-run:
	@echo ">>> [FAZ-TUDO] Iniciando configuração completa do ambiente..."
	@$(MAKE) setup
	@$(MAKE) migrate
	@$(MAKE) run

run:
	@echo ">>> Iniciando a aplicação em modo de desenvolvimento..."
	@export PYTHONPATH=$(shell pwd) && \
	export FLASK_APP=src.app && \
	export FLASK_DEBUG=True && \
	.venv/bin/flask run

fresh-run:
	# Garante que o ambiente virtual exista antes de continuar.
	@if [ ! -d ".venv" ]; then \
		$(MAKE) setup; \
	fi
	@echo ">>> [FRESH RUN] Removendo banco de dados antigo..."
	@rm -f data/meu_dash.db
	@$(MAKE) migrate
	@$(MAKE) run

test:
	@echo ">>> Executando testes com pytest..."
	@export PYTHONPATH=$(shell pwd) && \
	.venv/bin/pytest

# Aplica as migrações do banco de dados.
# Garante que o ambiente de migrações esteja configurado e que a migração inicial seja criada, se necessário.
migrate:
	@echo ">>> Aplicando migrações do banco de dados..."
	@if [ ! -d "migrations" ]; then \
		echo ">>> Diretório 'migrations' não encontrado. Executando 'flask db init'..."; \
		export PYTHONPATH=$(shell pwd) && export FLASK_APP=src.app && .venv/bin/flask db init; \
	fi
	# Verifica se há scripts de migração. Se não houver, cria a migração inicial.
	@if [ -z "$$(ls -A migrations/versions 2>/dev/null)" ]; then \
		echo ">>> Nenhuma migração inicial encontrada. Criando migração inicial..."; \
		export PYTHONPATH=$(shell pwd) && export FLASK_APP=src.app && .venv/bin/flask db migrate -m "Initial migration"; \
	fi
	@echo ">>> Aplicando migrações ao banco de dados (flask db upgrade)..."
	@export PYTHONPATH=$(shell pwd) && export FLASK_APP=src.app && .venv/bin/flask db upgrade

format:
	@echo ">>> Formatando o código com ruff..."
	@.venv/bin/ruff format .

lint:
	@echo ">>> Executando linter com ruff (com auto-correção)..."
	@.venv/bin/ruff check --fix .

security-scan:
	@echo ">>> Verificando vulnerabilidades de segurança com bandit..."
	@.venv/bin/bandit -r src -ll -ii

check:
	@echo ">>> Verificando formatação com ruff..."
	@.venv/bin/ruff format --check .
	@echo ">>> Verificando código com ruff check..."
	@.venv/bin/ruff check .
	@$(MAKE) security-scan

validate:
	@echo ">>> Executando validação completa..."
	@if [ ! -d ".venv" ]; then \
		echo ">>> Ambiente virtual não encontrado. Configurando automaticamente..."; \
		$(MAKE) setup; \
	fi
	@$(MAKE) install
	@$(MAKE) format
	@$(MAKE) test
	@echo ">>> ✅ Validação completa concluída com sucesso."

clean:
	@echo ">>> Removendo caches e arquivos temporários..."

	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -f .coverage

distclean: clean
	@echo ">>> [DEEP CLEAN] Removendo ambiente virtual, banco de dados, migrações e relatórios..."
	@rm -rf .venv
	@rm -rf migrations
	@rm -f data/meu_dash.db
	@echo ">>> Limpando diretórios de dados (uploads e reports)..."
	@rm -rf data/uploads/*
	@rm -rf data/reports/*
	@echo ">>> Limpeza completa concluída."

docker-build:
	@echo ">>> Construindo imagem Docker: $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)..."
	@docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) .

docker-run:
	@echo ">>> Executando container Docker..."
	@docker run -p 5000:5000 -v $(shell pwd)/data:/app/data $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)



