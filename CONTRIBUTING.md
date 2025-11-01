# 🤝 Guia de Contribuição para o `meu-dash`

Ficamos felizes com o seu interesse em contribuir para o projeto! Este guia fornece todas as informações necessárias para você começar.

## 🚀 Filosofia de Desenvolvimento: CI/CD-First

Este projeto adota uma filosofia **CI/CD-First**. Isso significa que abandonamos o uso de ambientes locais com `docker-compose` para evitar a "deriva de ambiente" (problemas que só acontecem em produção).

Todo o ciclo de vida do desenvolvimento (teste, build, deploy) é centralizado no pipeline de Integração Contínua e Entrega Contínua (CI/CD) do GitHub Actions. O fluxo de trabalho padrão é:

1. **Codificar Localmente:** Faça suas alterações no código-fonte.
2. **Versionar:** Faça o commit das suas alterações em uma nova branch (`git commit`).
3. **Disparar a Automação:** Envie suas alterações para o GitHub (`git push`).
4. **Validação Automática:** O pipeline de CI/CD irá automaticamente:
    - Executar os testes de backend e frontend.
    - Realizar a análise de segurança e qualidade do código.
    - Construir a imagem Docker de produção.
    - Publicar a imagem no registry (Docker Hub).
5. **Deploy (Opcional/Manual):** Com a imagem validada e publicada, você pode implantá-la no seu ambiente Kubernetes.

Este processo garante que cada alteração seja validada contra a mesma configuração que será usada em produção.

---

## 🛠️ Configuração do Ambiente de Desenvolvimento Local

Embora o `docker-compose` não seja mais usado para rodar a aplicação, você ainda precisa das ferramentas de desenvolvimento instaladas localmente para codificar e rodar verificações pontuais.

1. **Pré-requisitos:**
    - Python 3.12+
    - Node.js 20+
    - `make`

2. **Instalação de Dependências:**
    O `Makefile.mk` ainda contém comandos úteis para gerenciar dependências locais.

    ```bash
    # Instala dependências do backend (cria um .venv)
    make install-backend

    # Instala dependências do frontend
    make install-frontend
    ```

## 🔑 Configurando Segredos para Produção (Kubernetes)

Em um ambiente de produção, os segredos (como `ADMIN_USER`, `ADMIN_PASSWORD`, `SECRET_KEY`) **NUNCA** devem ser armazenados no código-fonte. Eles devem ser gerenciados através de **Kubernetes Secrets**.

## Passo 1: Criação Manual do Secret (se necessário)

Você pode criar o Secret diretamente no seu cluster Kubernetes com o seguinte comando. O `kubernetes.yaml` já está configurado para procurar um Secret com o nome `admin-token-secret`.

```bash
# Substitua 'seu-token-super-secreto-de-producao' pelo valor real
kubectl create secret generic smart-remedy-secrets \
  --from-literal=ADMIN_TOKEN='seu-token-super-secreto-de-producao' \
  --namespace=meu-dash-alertas
```

## Passo 2: Integração com Pipelines de CI/CD (GitHub Actions, Azure DevOps)

A melhor prática é automatizar a criação do Secret durante o deploy. O fluxo é o seguinte:

1. **Armazene o Token na Plataforma de CI/CD:** Guarde o valor do seu token como um segredo na sua ferramenta de CI/CD.
    - **GitHub Actions:** Vá em `Settings > Secrets and variables > Actions` e crie um novo "Repository secret" (ex: `ADMIN_TOKEN_PROD`).
    - **Azure DevOps:** Use "Variable groups" e marque a variável como secreta.

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

## ✅ Padrões de Código e Qualidade

Para manter o código limpo, consistente e seguro, utilizamos a ferramenta **Ruff** para formatação e linting, e **Bandit** para análise de segurança. O `Makefile` fornece comandos para simplificar o uso.

- **Para formatar seu código:**

    ```bash
    make format  # Usa o Ruff para formatar automaticamente o código
    ```

- **Para corrigir erros de linting automaticamente:**

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
