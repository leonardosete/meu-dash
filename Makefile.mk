# Makefile para automação de tarefas comuns no projeto meu-dash

# Define o interpretador Python a ser usado. Procura por um ambiente virtual.
PYTHON := $(shell if [ -d ".venv" ]; then echo ".venv/bin/python"; else echo "python3"; fi)

# Define o nome da imagem Docker de desenvolvimento e a tag.
DOCKER_IMAGE_NAME := meu-dash
DOCKER_IMAGE_TAG := latest
DOCKER_PROD_IMAGE_NAME := sevenleo/smart-plan

.PHONY: help install setup setup-frontend run test test-backend-docker format lint check clean distclean docker-build docker-run docker-prune validate validate-all-docker validate-clean-docker up down migrate-docker lint-backend-docker format-backend-docker check-backend-docker lint-frontend-docker format-frontend-docker test-frontend-docker format-all-docker publish-prod test-e2e-docker test-e2e-prod
help:
	@echo "Comandos disponíveis:"
	@echo ""
	@echo "--- 🚀 Ambiente de Produção (Docker + K8s) ---"
	@echo "  make publish-prod   - Constrói e publica a imagem de produção para o Docker Hub."
	@echo ""
	@echo "--- ✅ Validação e Qualidade de Código (Local) ---"
	@echo "  make check          - Roda todas as verificações: formatação, linting e segurança (para CI)."
	@echo "  make format         - Formata o código com 'ruff format'."
	@echo "  make lint           - Executa o linter 'ruff check --fix' para corrigir erros."
	@echo "  make security-scan  - Roda a verificação de segurança com 'bandit'."
	@echo "  make test           - Executa os testes do backend com pytest."
	@echo ""
	@echo "--- 🧹 Limpeza ---"
	@echo "  make clean          - Remove arquivos temporários e caches."
	@echo "  make distclean      - Remove TODOS os arquivos gerados (venv, db, relatórios, node_modules)."
	@echo "  make docker-prune   - Remove imagens Docker não utilizadas (dangling images)."
	@echo ""
	@echo "--- 📦 Gerenciamento de Dependências (Local) ---"
	@echo "  make install        - Instala as dependências do requirements.txt localmente."
	@echo "  make setup          - Cria o ambiente virtual e instala as dependências do backend."

# Cria o ambiente virtual e instala as dependências nele.
setup:
	@echo ">>> Configurando ambiente virtual em .venv..."
	@python3 -m venv .venv
	@echo ">>> Atualizando pip e instalando dependências no ambiente virtual..."
	# Usamos .venv/bin/python explicitamente para garantir que estamos instalando
	# dentro do ambiente virtual, evitando o erro 'externally-managed-environment' (PEP 668).
	@.venv/bin/python -m pip install --upgrade pip -r backend/requirements.txt

install:
	@echo ">>> Instalando dependências de requirements.txt..."
	@$(PYTHON) -m pip install -r backend/requirements.txt

test:
	@echo ">>> Executando testes do backend com pytest..."
	@cd backend && $(PYTHON) -m pytest

format:
	@echo ">>> Formatando o código com ruff..."
	@$(PYTHON) -m ruff format .

lint:
	@echo ">>> Executando linter com ruff (com auto-correção)..."
	@$(PYTHON) -m ruff check --fix .

security-scan:
	@echo ">>> Verificando vulnerabilidades de segurança com bandit..."
	@$(PYTHON) -m bandit -r backend/src -ll -ii

check:
	@echo ">>> Verificando formatação com ruff..."
	@$(PYTHON) -m ruff format --check backend
	@echo ">>> Verificando código com ruff check..."
	@$(PYTHON) -m ruff check backend
	@$(MAKE) security-scan

clean:
	@echo ">>> Removendo caches e arquivos temporários..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -f .coverage

distclean: clean
	@echo ">>> [DEEP CLEAN] Removendo ambiente virtual, banco de dados, migrações e relatórios..."
	@rm -rf .venv
	@rm -rf frontend/node_modules
	@rm -rf frontend/dist
	@echo ">>> Limpeza completa concluída."

docker-prune:
	@echo ">>> Removendo imagens Docker não utilizadas..."
	@docker image prune -f

publish-prod:
	@echo ">>> Removendo imagem de produção local anterior (se existir)..."
	@docker rmi $(DOCKER_PROD_IMAGE_NAME):$(DOCKER_IMAGE_TAG) || true
	@echo ">>> Construindo e publicando uma nova imagem de produção para linux/amd64: $(DOCKER_PROD_IMAGE_NAME):$(DOCKER_IMAGE_TAG)..."
	@docker buildx build --platform linux/amd64 -t $(DOCKER_PROD_IMAGE_NAME):$(DOCKER_IMAGE_TAG) -f Dockerfile . --push --no-cache
	@echo ">>> Imagem publicada com sucesso!"
