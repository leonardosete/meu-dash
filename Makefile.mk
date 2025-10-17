# Makefile para automação de tarefas comuns no projeto meu-dash

# Define o interpretador Python a ser usado. Procura por um ambiente virtual.
PYTHON := $(shell if [ -d ".venv" ]; then echo ".venv/bin/python"; else echo "python3"; fi)

# Define o nome da imagem Docker de desenvolvimento e a tag.
DOCKER_IMAGE_NAME := meu-dash
DOCKER_IMAGE_TAG := latest
DOCKER_PROD_IMAGE_NAME := sevenleo/smart-plan

.PHONY: help install setup setup-frontend run test test-backend-docker format lint check clean distclean docker-build docker-run docker-prune validate validate-all-docker validate-clean-docker up down migrate-docker lint-backend-docker format-backend-docker check-backend-docker lint-frontend-docker format-frontend-docker test-frontend-docker format-all-docker publish-prod
help:
	@echo "Comandos disponíveis:"
	@echo ""
	@echo "--- 🐳 Ambiente de Desenvolvimento (Docker - RECOMENDADO) ---"
	@echo "  make up             - (Recomendado) Inicia todo o ambiente de desenvolvimento com Docker Compose."
	@echo "  make down           - Para todo o ambiente Docker Compose."
	@echo "  make migrate-docker - (Importante) Aplica as migrações do DB dentro do contêiner Docker."
	@echo ""
	@echo "--- 🚀 Ambiente de Produção (Docker + K8s) ---"
	@echo "  make publish-prod   - Constrói e publica a imagem de produção para o Docker Hub."
	@echo ""
	@echo "--- ✅ Validação e Testes (Docker) ---"
	@echo "  make validate-all-docker - (RECOMENDADO) Roda TODAS as validações (backend + frontend) no Docker."
	@echo "  make validate-clean-docker - Roda TODAS as validações a partir de um build limpo, sem cache."
	@echo "  make test-backend-docker   - Executa os testes do backend (pytest) no Docker."
	@echo "  make check-backend-docker  - Roda format, lint e security scan do backend no Docker."
	@echo "  make test-frontend-docker  - Executa os testes do frontend (vitest) no Docker."
	@echo "  make format-all-docker   - Formata o código do backend e do frontend no Docker."
	@echo "  make format-backend-docker - Formata o código do backend com ruff no Docker."
	@echo "  make lint-frontend-docker  - Roda o linter (eslint) do frontend no Docker."
	@echo "  make format-frontend-docker- Formata o código do frontend com Prettier no Docker."
	@echo ""
	@echo "--- 🧹 Limpeza ---"
	@echo "  make clean          - Remove arquivos temporários e caches."
	@echo "  make distclean      - Remove TODOS os arquivos gerados (venv, db, relatórios, node_modules)."
	@echo "  make docker-prune   - Remove imagens Docker não utilizadas (dangling images)."
	@echo ""
	@echo "--- 📜 Comandos Legados / Locais (NÃO RECOMENDADOS) ---"
	@echo "  make install        - (Legado) Instala as dependências do requirements.txt localmente."
	@echo "  make setup          - (Legado) Cria o ambiente virtual e instala as dependências do backend."
	@echo "  make setup-and-run  - (Legado) Configura o ambiente local do zero e inicia a aplicação."
	@echo "  make run            - (Legado) Inicia a aplicação Flask localmente."
	@echo "  make fresh-run      - (Legado) Limpa o DB, aplica migrações e inicia a aplicação localmente."
	@echo "  make migrate        - (Legado) Aplica as migrações do banco de dados localmente."
	@echo "  make format         - Formata o código com 'ruff format'."
	@echo "  make lint           - Executa o linter 'ruff check --fix' para corrigir erros."
	@echo "  make security-scan  - Roda a verificação de segurança com 'bandit'."
	@echo "  make check          - Roda todas as verificações: formatação, linting e segurança (para CI)."
	@echo "  make validate       - (TUDO-EM-UM) Instala dependências, formata e testa o projeto."
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
	@echo ">>> A criação inicial do DB agora é automática. Este comando é para futuras alterações de esquema."
	@docker-compose exec -T backend sh -c "flask db init --directory backend/migrations || true"
	@docker-compose exec -T backend flask db migrate -m "Autodetect database changes" --directory backend/migrations
	@docker-compose exec -T backend flask db upgrade --directory backend/migrations

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
	@docker-compose run --rm security-scanner bandit -r src -ll -ii

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

format-all-docker:
	@echo ">>> [DOCKER] Formatando todo o código (Backend + Frontend)..."
	@$(MAKE) format-backend-docker
	@$(MAKE) format-frontend-docker

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
	# A forma correta de remover volumes gerenciados pelo Docker (como node_modules) é com 'down --volumes'.
	# Isso resolve o problema de permissão sem precisar de 'sudo'.
	@echo ">>> Parando contêineres e removendo volumes gerenciados pelo Docker (incluindo node_modules)..."
	@docker-compose down --volumes --remove-orphans
	# Remove o diretório de dados local, caso exista de execuções antigas.
	@echo ">>> Limpando diretório de dados local legado..."
	@rm -rf data
	@rm -rf .venv
	@rm -rf backend/migrations
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
	@echo ">>> Ambiente iniciado. Backend e Frontend estão em execução."

down:
	@echo ">>> Parando ambiente de desenvolvimento Docker Compose..."
	@docker-compose down --remove-orphans

docker-prune:
	@echo ">>> Removendo imagens Docker não utilizadas..."
	@docker image prune -f

publish-prod:
	@echo ">>> Construindo e publicando a imagem de produção multi-plataforma: $(DOCKER_PROD_IMAGE_NAME):$(DOCKER_IMAGE_TAG)..."
	@echo ">>> Construindo para linux/amd64 (cluster) e linux/arm64 (local)..."
	@docker buildx build --platform linux/amd64,linux/arm64 -t $(DOCKER_PROD_IMAGE_NAME):$(DOCKER_IMAGE_TAG) -f Dockerfile . --push
	@echo ">>> Imagem publicada com sucesso!"
