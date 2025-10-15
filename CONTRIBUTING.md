# 🤝 Guia de Contribuição para o `meu-dash`

Ficamos felizes com o seu interesse em contribuir para o projeto! Este guia fornece todas as informações necessárias para você começar.

## 🛠️ Configuração do Ambiente de Desenvolvimento

O método recomendado para o desenvolvimento é usar **Docker Compose**, que garante um ambiente isolado e consistente.

1. **Pré-requisitos:** Docker e Docker Compose instalados.

2. **Inicie o Ambiente Completo:**
   Este comando constrói e inicia os contêineres para o backend e o frontend.

   ```bash
   make up
   ```

3. **Prepare o Banco de Dados (Primeira Vez ou Após Limpeza):**
   Após iniciar os contêineres, execute este comando para criar e aplicar as migrações do banco de dados. **Este passo é crucial.**

   ```bash
   make migrate-docker
   ```

   Este passo é crucial para que a API funcione corretamente.

Após a execução, a API estará disponível em `http://127.0.0.1:5001` e o frontend em `http://127.0.0.1:5174` (ou as portas definidas no seu arquivo `.env`).
Para parar tudo, use `make down`.

### Método Legado (Ambiente Virtual Local)

Se por algum motivo você não puder usar Docker, o método antigo de configuração com ambiente virtual ainda está disponível. Use `make setup-and-run` para configurar e iniciar apenas o backend.

### 📦 Instalando ou Atualizando Dependências

Se você já tem o ambiente configurado, mas precisa instalar novas dependências que foram adicionadas ao `requirements.txt` (como no caso do `PyJWT`), use o comando:

```bash
make install
```

Isso garantirá que seu ambiente virtual esteja sempre sincronizado com o projeto.

## 🚀 Executando a Aplicação Localmente

Após a configuração inicial com `make setup-and-run`, nos dias seguintes você pode parar e iniciar o servidor de desenvolvimento usando apenas:

```bash
make run
```

A aplicação estará disponível em `http://127.0.0.1:5000`.

### 🔑 Configurando Funcionalidades de Administrador

A aplicação utiliza um token secreto para proteger funcionalidades administrativas. A forma de configurar este token difere entre o ambiente de desenvolvimento local e o de produção.

#### Para Desenvolvimento Local

Para testar funcionalidades protegidas localmente, você precisa definir a variável de ambiente `ADMIN_TOKEN`. Execute o seguinte comando no seu terminal **antes** de iniciar a aplicação:

```bash
# Você pode usar qualquer valor para o seu token secreto
export ADMIN_TOKEN="seu-token-secreto-aqui"
```

Após definir o token e iniciar a aplicação com `make run` ou `make fresh-run`, você poderá acessar a área administrativa para fazer o login.

#### Para Produção (Kubernetes): Gerenciamento de Segredos

Em um ambiente de produção, o token **NUNCA** deve ser armazenado no código-fonte ou em arquivos de manifesto. Ele é um segredo e deve ser gerenciado através de **Kubernetes Secrets**.

## Passo 1: Criação Manual do Secret (se necessário)

Você pode criar o Secret diretamente no seu cluster Kubernetes com o seguinte comando. O `kubernetes.yaml` já está configurado para procurar um Secret com o nome `admin-token-secret`.

```bash
# Substitua 'seu-token-super-secreto-de-producao' pelo valor real
kubectl create secret generic admin-token-secret \
  --from-literal=ADMIN_TOKEN='seu-token-super-secreto-de-producao' \
  --namespace=meu-dash-alertas
```

## Passo 2: Integração com Pipelines de CI/CD (GitHub Actions, Azure DevOps)

A melhor prática é automatizar a criação do Secret durante o deploy. O fluxo é o seguinte:

1. **Armazene o Token na Plataforma de CI/CD:** Guarde o valor do seu token como um segredo na sua ferramenta de CI/CD.
    * **GitHub Actions:** Vá em `Settings > Secrets and variables > Actions` e crie um novo "Repository secret" (ex: `ADMIN_TOKEN_PROD`).
    * **Azure DevOps:** Use "Variable groups" e marque a variável como secreta.

2. **Use o Segredo no Pipeline:** No seu script de pipeline, use a variável para criar ou recenteizar o Kubernetes Secret de forma segura. O comando `kubectl apply` com `--dry-run` é uma forma robusta de fazer isso.

    *Exemplo conceitual para um passo no GitHub Actions:*

    ```yaml
    - name: Create or Update Kubernetes Secret
      run: |
        kubectl create secret generic admin-token-secret \
          --from-literal=ADMIN_TOKEN='${{ secrets.ADMIN_TOKEN_PROD }}' \
          --namespace=meu-dash-alertas \
          --dry-run=client -o yaml | kubectl apply -f -
    ```

Este processo garante que o valor real do token nunca seja exposto, sendo injetado de forma segura no cluster apenas durante o processo de implantação.

## 🧹 Limpando o Ambiente

Para redefinir completamente seu ambiente de desenvolvimento, removendo todos os arquivos gerados (ambiente virtual, banco de dados, relatórios, etc.), execute:

```bash
make distclean
```

Este comando é útil quando você quer começar do zero, como se tivesse acabado de clonar o repositório. Após a limpeza, você pode executar `make setup-and-run` para reconfigurar tudo.

### 🗄️ Banco de Dados

A aplicação usa Flask-Migrate para gerenciar o esquema do banco de dados. O `Makefile` automatiza este processo.

* **Para aplicar novas migrações** ou garantir que o banco de dados esteja recenteizado, execute:

    ```bash
    make migrate
    ```

## ✅ Padrões de Código e Qualidade

Para manter o código limpo, consistente e seguro, utilizamos a ferramenta **Ruff** para formatação e linting, e **Bandit** para análise de segurança. O `Makefile` fornece comandos para simplificar o uso.

* **Para formatar seu código:**

    ```bash
    make format  # Usa o Ruff para formatar automaticamente o código
    ```

* **Para corrigir erros de linting automaticamente:**

    ```bash
    make lint    # Usa o Ruff para corrigir o que for possível (`ruff check --fix`)
    ```

Antes de submeter seu código, é uma boa prática rodar o verificador completo, que garante que o código está formatado, sem erros de linting e sem vulnerabilidades de segurança conhecidas. Este comando espelha as verificações feitas no pipeline de CI:

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
