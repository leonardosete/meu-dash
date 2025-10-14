# Makefile para automação de tarefas comuns no projeto meu-dash

# Define o interpretador Python a ser usado. Procura por um ambiente virtual.
PYTHON := $(shell if [ -d ".venv" ]; then echo ".venv/bin/python"; else echo "python3"; fi)

# Define o nome da imagem Docker e a tag.
DOCKER_IMAGE_NAME := meu-dash
DOCKER_IMAGE_TAG := latest

.PHONY: help install setup setup-frontend run test test-backend-docker format lint check clean distclean docker-build docker-run docker-prune validate validate-all-docker validate-clean-docker up down migrate-docker lint-backend-docker format-backend-docker check-backend-docker lint-frontend-docker format-frontend-docker test-frontend-docker start-frontend-docker

help:
	@echo "Comandos disponíveis:"
	@echo "  make install        - Instala as dependências do requirements.txt."
	@echo "  make setup          - (Legado) Cria o ambiente virtual e instala as dependências do backend."
	@echo "  make migrate-docker - (Recomendado) Aplica as migrações do DB dentro do contêiner Docker."
	@echo "  make setup-frontend - Cria a estrutura inicial do projeto frontend com Vite e React."
	@echo "  make setup-and-run  - (Legado) Configura o ambiente do zero e inicia a aplicação."
	@echo "  make run            - (Legado) Inicia a aplicação Flask em modo de desenvolvimento."
	@echo "  make start-frontend-docker - Inicia o servidor de desenvolvimento do frontend no Docker."
	@echo "  make fresh-run      - Limpa o DB, aplica migrações e inicia a aplicação (para testes)."
	@echo "  make up             - (Recomendado) Inicia todo o ambiente de desenvolvimento com Docker Compose."
	@echo "  make down           - Para todo o ambiente Docker Compose."
	@echo "  make migrate        - Aplica as migrações do banco de dados."
	@echo ""
	@echo "  --- Validação e Testes (Docker) ---"
	@echo "  make validate-all-docker - (RECOMENDADO) Roda TODAS as validações (backend + frontend) no Docker."
	@echo "  make validate-clean-docker - Roda TODAS as validações a partir de um build limpo, sem cache."
	@echo "  make test-backend-docker   - Executa os testes do backend (pytest) no Docker."
	@echo "  make check-backend-docker  - Roda format, lint e security scan do backend no Docker."
	@echo "  make test-frontend-docker  - Executa os testes do frontend (vitest) no Docker."
	@echo "  make lint-frontend-docker  - Roda o linter (eslint) do frontend no Docker."
	@echo "  make format         - Formata o código com 'ruff format'."
	@echo "  make lint           - Executa o linter 'ruff check --fix' para corrigir erros."
	@echo "  make security-scan  - Roda a verificação de segurança com 'bandit'."
	@echo "  make check          - Roda todas as verificações: formatação, linting e segurança (para CI)."
	@echo "  make validate       - (TUDO-EM-UM) Instala dependências, formata e testa o projeto."
	@echo "  make clean          - Remove arquivos temporários e caches."
	@echo "  make distclean      - Remove TODOS os arquivos gerados (venv, db, relatórios)."
	@echo ""
	@echo "  --- Comandos Legados / Locais ---"
	@echo "  make docker-prune   - Remove imagens Docker não utilizadas (dangling images)."
	@echo "  make docker-build   - Constrói a imagem Docker da aplicação."
	@echo "  make docker-run     - Executa a aplicação a partir da imagem Docker."

# Cria o ambiente virtual e instala as dependências nele.
setup:
	@echo ">>> Configurando ambiente virtual em .venv..."
	@python3 -m venv .venv
	@echo ">>> Atualizando pip e instalando dependências no ambiente virtual..."
	@.venv/bin/pip install --upgrade pip -r backend/requirements.txt

install:
	@echo ">>> Instalando dependências de requirements.txt..."
	@$(PYTHON) -m pip install -r backend/requirements.txt

setup-and-run:
	@echo ">>> [FAZ-TUDO] Iniciando configuração completa do ambiente..."
	@$(MAKE) setup
	@$(MAKE) migrate
	@$(MAKE) run

run:
	@echo ">>> Iniciando a aplicação em modo de desenvolvimento..."
	@export PYTHONPATH=$(shell pwd)/backend && \
	export FLASK_APP=src.app && \
	export FLASK_DEBUG=True && \
	.venv/bin/flask run --port=${BACKEND_PORT:-5000}

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
	@export PYTHONPATH=$(shell pwd)/backend && \
	.venv/bin/pytest

migrate-docker:
	@echo ">>> Gerenciando migrações do banco de dados dentro do contêiner Docker..."
	@# Garante que o diretório de migrações exista, inicializando se necessário.
	@docker-compose exec -T backend sh -c "if [ ! -d 'migrations' ]; then echo '>>> Inicializando diretório de migrações...'; flask db init; fi"
	@# Verifica se há scripts de migração. Se não houver, cria a migração inicial.
	@docker-compose exec -T backend sh -c "if [ -z \"\$$(ls -A migrations/versions 2>/dev/null)\" ]; then \
		echo '>>> Criando migração inicial...'; \
		flask db migrate -m 'Initial migration'; \
	fi"
	@# Aplica as migrações pendentes ao banco de dados.
	@echo ">>> Aplicando migrações ao banco de dados (flask db upgrade)..."
	@docker-compose exec -T backend flask db upgrade

# Aplica as migrações do banco de dados.
# Garante que o ambiente de migrações esteja configurado e que a migração inicial seja criada, se necessário.
migrate:
	@echo ">>> Aplicando migrações do banco de dados..."
	@if [ ! -d "backend/migrations" ]; then \
		echo ">>> Diretório 'migrations' não encontrado. Executando 'flask db init'..."; \
		export PYTHONPATH=$(shell pwd)/backend && export FLASK_APP=src.app && .venv/bin/flask db init; \
	fi
	# Verifica se há scripts de migração. Se não houver, cria a migração inicial.
	@if [ -z "$$(ls -A backend/migrations/versions 2>/dev/null)" ]; then \
		echo ">>> Nenhuma migração inicial encontrada. Criando migração inicial..."; \
		export PYTHONPATH=$(shell pwd)/backend && export FLASK_APP=src.app && .venv/bin/flask db migrate -m "Initial migration"; \
	fi
	@echo ">>> Aplicando migrações ao banco de dados (flask db upgrade)..."
	@export PYTHONPATH=$(shell pwd)/backend && export FLASK_APP=src.app && .venv/bin/flask db upgrade

format:
	@echo ">>> Formatando o código com ruff..."
	@.venv/bin/ruff format .

lint:
	@echo ">>> Executando linter com ruff (com auto-correção)..."
	@.venv/bin/ruff check --fix .

security-scan:
	@echo ">>> Verificando vulnerabilidades de segurança com bandit..."
	@.venv/bin/bandit -r backend/src -ll -ii

# --- Comandos de Validação e Testes no Docker ---

lint-backend-docker:
	@echo ">>> [DOCKER] Executando linter com ruff (com auto-correção)..."
	@docker-compose exec -T backend ruff check --fix .

format-backend-docker:
	@echo ">>> [DOCKER] Formatando o código do backend com ruff..."
	@docker-compose exec -T backend ruff format .

check-backend-docker:
	@echo ">>> [DOCKER] Verificando formatação e linting do backend com ruff..."
	@docker-compose exec -T backend ruff format --check .
	@docker-compose exec -T backend ruff check .
	@echo ">>> [DOCKER] Verificando segurança do backend com bandit..."
	@docker-compose exec -T security-scanner bandit -r src -ll -ii

test-backend-docker:
	@echo ">>> [DOCKER] Executando testes do backend com pytest..."
	@docker-compose exec -T backend pytest

lint-frontend-docker:
	@echo ">>> [DOCKER] Executando linter do frontend com ESLint..."
	@docker-compose exec -T frontend npm run lint

format-frontend-docker:
	@echo ">>> [DOCKER] Formatando o código do frontend com Prettier..."
	@docker-compose exec -T frontend npm run format

test-frontend-docker:
	@echo ">>> [DOCKER] Executando testes do frontend..."
	@docker-compose exec -T frontend npm run test

start-frontend-docker:
	@echo ">>> [DOCKER] Iniciando servidor de desenvolvimento do frontend (Vite)..."
	@docker-compose exec -d frontend npm run dev

validate-clean-docker:
	@echo ">>> [DOCKER] Executando validação completa a partir de um build limpo (sem cache)..."
	@echo ">>> Passo 1: Destruindo ambiente Docker existente (incluindo volumes)..."
	@docker-compose down --volumes --remove-orphans
	@echo ">>> Passo 2: Forçando a reconstrução de todas as imagens sem cache..."
	@docker-compose build --no-cache
	@$(MAKE) validate-all-docker

validate-all-docker:
	@echo ">>> [DOCKER] Executando validação completa (Backend + Frontend)..."
	@echo ">>> Garantindo que todos os serviços estão em execução..."
	@$(MAKE) up
	@$(MAKE) check-backend-docker && $(MAKE) test-backend-docker && $(MAKE) lint-frontend-docker && $(MAKE) test-frontend-docker

check:
	@echo ">>> Verificando formatação com ruff..."
	@.venv/bin/ruff format --check backend
	@echo ">>> Verificando código com ruff check..."
	@.venv/bin/ruff check backend
	@$(MAKE) security-scan

validate:
	@echo ">>> Executando validação completa: instalando dependências, formatando e testando..."
	@$(MAKE) install
	@$(MAKE) format
	@$(MAKE) test
	@echo ">>> Validação completa concluída com sucesso."

clean:
	@echo ">>> Removendo caches e arquivos temporários..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -f .coverage

distclean: clean
	@echo ">>> [DEEP CLEAN] Removendo ambiente virtual, banco de dados, migrações e relatórios..."
	@rm -rf .venv
	@rm -rf frontend/node_modules frontend/dist
	@rm -rf backend/migrations
	@rm -f data/meu_dash.db
	@echo ">>> Limpando diretórios de dados (uploads e reports)..."
	@rm -rf data/uploads/*
	@rm -rf data/reports/*
	@echo ">>> Limpeza completa concluída."

docker-build:
	@echo ">>> Construindo imagem Docker: $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)..."
	@docker build -f backend/Dockerfile -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) ./backend

docker-run:
	@echo ">>> Executando container Docker..."
	@docker run -p 5000:5000 -v $(shell pwd)/data:/app/data $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)

up:
	@echo ">>> Iniciando ambiente de desenvolvimento com Docker Compose..."
	@docker-compose up --build -d
	@$(MAKE) start-frontend-docker

down:
	@echo ">>> Parando ambiente de desenvolvimento Docker Compose..."
	@docker-compose down --remove-orphans

docker-prune:
	@echo ">>> Removendo imagens Docker não utilizadas..."
	@docker image prune -f
