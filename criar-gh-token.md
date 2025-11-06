# 🔐 Configurar GitHub App para o Feedback Automático

> **Atualização:** o mecanismo de feedback agora utiliza um **GitHub App** em vez de um Personal Access Token (PAT). Isso reduz permissões, aplica rotação automática de tokens e facilita auditoria.

## 🎯 Objetivo

Configurar um GitHub App com permissão de criação de issues para que o SmartRemedy registre feedbacks automaticamente no repositório `meu-dash`.

---

## 1. Criar o GitHub App

1. Acesse [Settings → Developer settings → GitHub Apps](https://github.com/settings/apps).
2. Clique em **New GitHub App** e preencha:

   - **GitHub App name:** `smartremedy-feedback`
   - **Homepage URL:** `https://github.com/leonardosete/meu-dash`
   - **Webhook:** mantenha desativado (não é necessário).
   - **Repository permissions:**
     - *Issues* → **Read & write** (única permissão exigida).
   - **Subscribe to events:** nenhum evento obrigatório.
   - **Where can this GitHub App be installed?** → `Only on this account` (ajuste conforme a conta ou organização).
3. Salve o App. Na tela seguinte:

   - Clique em **Generate a private key** e baixe o arquivo `.pem`.
   - Anote o **App ID** exibido na coluna direita.

---

## 2. Instalar o App no repositório

1. Na página do App recém-criado, clique em **Install App**.
2. Escolha `Install` na conta relevante (ex.: `leonardosete`).
3. Marque apenas o repositório `meu-dash` e confirme.
4. Após a instalação, observe a URL: o trecho `/installations/<ID>` contém o **Installation ID** necessário para a aplicação.

---

## 3. Configurar variáveis de ambiente

Defina os segredos no ambiente (Kubernetes, `.env`, etc.):

    GITHUB_APP_ID=<App ID fornecido pelo GitHub>
    GITHUB_APP_INSTALLATION_ID=<Installation ID anotado>

    # Opção A — chave inline
    GITHUB_APP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"

    # Opção B — chave em arquivo (ex.: Secret montado em volume)
    GITHUB_APP_PRIVATE_KEY_PATH=/app/secrets/github-app.pem

    # Opcionais — sobrescrevem os padrões
    GITHUB_REPO_OWNER=leonardosete
    GITHUB_REPO_NAME=meu-dash

> **Importante:** se utilizar `GITHUB_APP_PRIVATE_KEY`, substitua quebras de linha reais por `\n` ao definir a variável.

---

## 4. Validar a integração

1. Reinicie a aplicação para carregar as novas variáveis.
2. Envie um feedback de teste pelo modal do SmartRemedy.
3. Verifique se uma issue foi criada automaticamente no GitHub.
4. Consulte os logs do backend para confirmar a geração do token e o POST na API.

Teste manual opcional com token de instalação válido:

    curl -X POST \
      -H "Authorization: Bearer <TOKEN_DE_INSTALACAO>" \
      -H "Accept: application/vnd.github+json" \
      https://api.github.com/repos/leonardosete/meu-dash/issues \
      -d '{"title": "Teste", "body": "Issue via GitHub App."}'

---

## 5. Rotina de manutenção

- Proteja a chave privada (armazenar em Secret, acesso restrito).
- Rotacione a chave pelo botão **Generate a new private key** sempre que necessário.
- Para revogar acesso, remova a instalação ou exclua o App.
- Monitore o uso via **Audit log** (organizações) ou registros de atividade do GitHub.

---

## 6. Troubleshooting rápido

| Sintoma | Possível causa | Ação sugerida |
| --- | --- | --- |
| `Serviço de feedback indisponível` | Variáveis do App ausentes ou chave inválida | Revisar `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID` e chave privada |
| `401 Unauthorized` | Token de instalação não gerado ou expirado | Verificar sincronismo de relógio, checar logs para renovação do token |
| `404 Not Found` | App não instalado no repositório alvo | Reinstalar o App e confirmar `Installation ID` |
| `Validation Failed` | Payload inválido (ex.: título vazio) | Conferir dados enviados pelo frontend |

---

## 7. FAQ

- **Ainda preciso do `GITHUB_TOKEN`?** Não. O fluxo agora depende apenas do GitHub App.
- **Consigo usar o mesmo App em múltiplos repositórios?** Sim — basta selecioná-los durante a instalação ou repetir o processo em outra conta ou organização.
- **Posso deixar um fallback para PAT?** Não recomendado; o código atual não mantém esse caminho.

Com o GitHub App configurado, o SmartRemedy envia feedbacks com privilégios mínimos e segurança reforçada. ✅

