# 🤝 Guia de Contribuição para o `meu-dash`

Ficamos felizes com o seu interesse em contribuir para o projeto! Este guia fornece todas as informações necessárias para você começar.

## 🛠️ Configuração do Ambiente de Desenvolvimento

O projeto utiliza um `Makefile` para automatizar todo o processo de configuração. Para preparar seu ambiente, siga os passos:

1. **Clone o repositório:**

    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd meu-dash
    ```

2. **Execute o setup automatizado:**
    Este comando irá criar o ambiente virtual, instalar todas as dependências e deixar o projeto pronto para ser executado.

    ```bash
    make setup
    ```

## 🚀 Executando a Aplicação Localmente

Com o ambiente configurado, basta executar o seguinte comando para iniciar o servidor de desenvolvimento:

```bash
make run
```

A aplicação estará disponível em `http://127.0.0.1:5000`.

Para o setup inicial do banco de dados, pode ser necessário rodar os comandos de migração manualmente. Consulte a seção de banco de dados abaixo.

### 🗄️ Banco de Dados

A aplicação usa Flask-Migrate para gerenciar o esquema do banco de dados.

- **Primeira vez:** Se for a primeira configuração, inicialize o banco de dados:

    ```bash
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```

- **Atualizações futuras:** Para aplicar novas migrações, execute:

    ```bash
    flask db upgrade
    ```

## ✅ Padrões de Código e Qualidade

Para manter o código limpo, consistente e livre de erros, utilizamos a ferramenta **Ruff**. O `Makefile` fornece comandos para simplificar o uso.

- **Para formatar seu código:**

    ```bash
    make format
    ```

- **Para corrigir erros de linting automaticamente:**

    ```bash
    make lint
    ```

Antes de submeter seu código, é uma boa prática rodar o verificador completo, que garante que o código está formatado e sem erros de linting:

```bash
make check
```

## 🧪 Executando os Testes

Para garantir que suas alterações não quebraram nenhuma funcionalidade, execute a suíte de testes com `pytest` através do Makefile:

```bash
make test
```

Certifique-se de que todos os testes passam antes de abrir um Pull Request.

## 📄 Processo de Pull Request (PR)

1. **Crie uma nova branch:** (`git checkout -b feature/minha-feature`).
2. **Faça suas alterações.**
3. **Garanta a qualidade do código:** Rode `make check` e `make test` para formatar, lintar e testar seu código.
4. **Faça o commit:** Escreva uma mensagem de commit clara e concisa.
5. **Abra o Pull Request:** Envie o PR para a branch `main`. Descreva suas alterações e o motivo delas.
