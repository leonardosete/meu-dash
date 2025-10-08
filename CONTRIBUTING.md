# 🤝 Guia de Contribuição para o `meu-dash`

Ficamos felizes com o seu interesse em contribuir para o projeto! Este guia fornece todas as informações necessárias para você começar.

## 🛠️ Configuração do Ambiente de Desenvolvimento

Para facilitar o desenvolvimento e garantir a consistência, recomendamos o uso de um ambiente virtual Python.

1.  **Clone o repositório:**

    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd meu-dash
    ```

2.  **Crie e ative um ambiente virtual:**

    ```bash
    # Para macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate

    # Para Windows
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Instale as dependências:**

    O arquivo `requirements.txt` contém todas as dependências de produção e desenvolvimento.

    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Executando a Aplicação Localmente

Com as dependências instaladas, você pode iniciar a aplicação Flask no modo de desenvolvimento.

1.  **Inicialize o banco de dados (se for a primeira vez):**

    A aplicação usa Flask-Migrate para gerenciar o esquema do banco de dados. O banco de dados SQLite será criado automaticamente no diretório `data/`.

    ```bash
    # Estas variáveis de ambiente dizem ao Flask onde encontrar a aplicação
    export FLASK_APP=src/app.py

    # Aplica quaisquer migrações de banco de dados
    flask db upgrade
    ```

2.  **Inicie o servidor de desenvolvimento:**

    Para habilitar o modo de depuração com recarregamento automático, defina a variável de ambiente `FLASK_DEBUG`.

    ```bash
    export FLASK_DEBUG=True
    flask run
    ```

    A aplicação estará disponível em `http://127.0.0.1:5000`.

## ✅ Padrões de Código e Qualidade

Para manter o código limpo e consistente, utilizamos o formatador de código **Black**.

Antes de submeter seu código (fazer um commit), certifique-se de formatá-lo executando o Black na raiz do projeto:

```bash
black .
```

## 🧪 Executando os Testes

Utilizamos `pytest` para os testes. Para garantir que suas alterações não quebraram nenhuma funcionalidade existente, execute a suíte de testes:

```bash
pytest
```

Certifique-se de que todos os testes passam antes de abrir um Pull Request.

## 📄 Processo de Pull Request (PR)

1.  **Crie uma nova branch:** Crie uma branch descritiva para a sua feature ou correção (`git checkout -b feature/minha-feature` ou `git checkout -b fix/meu-bug`).
2.  **Faça suas alterações:** Implemente sua feature ou correção de bug.
3.  **Formate e teste seu código:** Execute `black .` e `pytest`.
4.  **Faça o commit:** Escreva uma mensagem de commit clara e concisa.
5.  **Abra o Pull Request:** Envie o PR para a branch principal do repositório.

No seu PR, descreva as alterações que você fez e por quê. Se o PR resolve uma issue existente, mencione-a na descrição (e.g., "Closes #123").
