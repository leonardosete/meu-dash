# 🤝 Guia de Contribuição para o `meu-dash`

Ficamos felizes com o seu interesse em contribuir para o projeto! Este guia fornece todas as informações necessárias para você começar.

## 🛠️ Configuração do Ambiente de Desenvolvimento

O projeto utiliza um `Makefile` para automatizar todo o processo de configuração. Para preparar seu ambiente, siga os passos:

1. **Clone o repositório:**

    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd meu-dash
    ```

2. **Execute o setup completo e inicie a aplicação:**
    Este comando único cuida de tudo: cria o ambiente virtual, instala dependências, inicializa o banco de dados e inicia o servidor.

    ```bash
    make setup-and-run
    ```

## 🚀 Executando a Aplicação Localmente

Após a configuração inicial com `make setup-and-run`, nos dias seguintes você pode parar e iniciar o servidor de desenvolvimento usando apenas:

```bash
make run
```

A aplicação estará disponível em `http://127.0.0.1:5000`.

## 🧹 Limpando o Ambiente

Para redefinir completamente seu ambiente de desenvolvimento, removendo todos os arquivos gerados (ambiente virtual, banco de dados, relatórios, etc.), execute:

```bash
make distclean
```

Este comando é útil quando você quer começar do zero, como se tivesse acabado de clonar o repositório. Após a limpeza, você pode executar `make setup-and-run` para reconfigurar tudo.

### 🗄️ Banco de Dados

A aplicação usa Flask-Migrate para gerenciar o esquema do banco de dados. O `Makefile` automatiza este processo.

- **Para aplicar novas migrações** ou garantir que o banco de dados esteja atualizado, execute:

    ```bash
    make migrate
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
6. **Faça suas alterações.**
