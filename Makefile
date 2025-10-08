# Makefile para automação de tarefas comuns do projeto meu-dash

# Garante que os comandos sejam executados mesmo que existam arquivos com o mesmo nome
.PHONY: all install apply-format format-check test check

# --- Alvo Padrão ---
# Executa a suíte de verificação completa por padrão ao rodar 'make'
all: check

# Instala as dependências do projeto
install:
	@echo "📦 Instalando dependências de requirements.txt..."
	@pip install -r requirements.txt

# Aplica a formatação do código com o Black
apply-format:
	@echo "🎨 Formatando o código com Black..."
	@black .

# Valida se o código está formatado corretamente com o Black (não modifica os arquivos)
format-check:
	@echo "🔍  Validando a formatação do código..."
	@black --check .

# Executa os testes com Pytest em modo verboso
test:
	@echo "🧪 Executando testes com Pytest..."
	@pytest -v

# Executa a suíte de verificação completa: valida a formatação e executa os testes.
# Ideal para rodar antes de um commit ou no pipeline de CI.
check: install
	@echo "\n--- Etapa 2/3: Validando a formatação do código... ---"
	@black --check .
	@echo "\n--- Etapa 3/3: Executando testes com Pytest... ---"
	@pytest -v
	@echo "\n✅ Verificação completa (instalação + formato + testes) concluída com sucesso!"
