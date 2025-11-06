# Plano de Ação Prioritário

> Histórico das fases anteriores permanece em `OLD_REFACTOR_PLAN.md`. Este arquivo lista apenas o estado atual das prioridades.

## 1. Painéis Concluídos

### 1.1 Feedback de Usuário (✅ Concluído)

- Backend `POST /api/v1/feedback` com validação e integração GitHub App
- `FeedbackModal` no frontend com formulário e preview
- Tipos TypeScript (`FeedbackData`) e testes backend cobrindo 5 cenários
- Labels criadas no GitHub e issues de teste validadas
- Guias atualizados (`docs/FEEDBACK_PLAN.md`, README) e PAT removido
- Fluxo validado em produção: issue #13 aberta automaticamente via GitHub App

## 2. Backend & Segurança

### 2.1 Instabilidade Crônica (✅ Concluído)

- Janela temporal parametrizada (`JANELA_INSTABILIDADE_HORAS`)
- Árvores de decisão e testes ajustados para eventos `Closed`
- Artefatos de teste dedicados adicionados

### 2.2 GitHub App (✅ Concluído)

- Helper `backend/src/github_app.py` com cache de tokens de instalação
- Rota `/api/v1/feedback` usa `Authorization: Bearer <installation_token>`
- Dependência `PyJWT[crypto]` adicionada para suportar RS256
- `criar-gh-token.md` reescrito com o fluxo de GitHub App
- GitHub App dedicado criado e instalado no repositório `leonardosete/meu-dash` — fluxo validado em produção (issue #13 criada automaticamente via GitHub App)

> **Lembrete:** `kubernetes/secrets.local.yaml` não é versionado. Antes de configurar AKS/Azure DevOps, gerar os Secrets oficiais (KeyVault/Secrets do cluster) com `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID` e `GITHUB_APP_PRIVATE_KEY` — **não esquecer** de migrar esses valores para o ambiente gerenciado.

## 3. Documentação & Comunicação

### 3.1 Doc Gerencial (Prioridade Alta)

- Reescrever seções “Desafio”, “Proposta de Valor”, “Como Usar”
- Atualizar screenshots e aprovar conteúdo com stakeholder

## 4. AKS, Azure DevOps & Helm

### 4.1 Helm Chart (Alta)

- Criar chart `charts/smart-remedy` (Deployment, Service, Ingress, ConfigMap, Secrets parametrizados)
- Converter `kubernetes-v3.yaml` em templates e `values.yaml`
- Externalizar Secrets para KeyVault/Azure Secrets (sem `secrets.local.yaml`)

### 4.2 Pipeline Azure DevOps (Alta)

- Pipeline YAML: build da imagem, push para ACR, package chart e deploy (helm upgrade)
- Configurar Service Connection (Service Principal) com push/pull no ACR
- Padronizar tags semânticas entre imagem e chart

### 4.3 Ingress & Rede (Alta)

- Definir controlador (NGINX/AGIC) para AKS
- Adaptar templates do chart para anotações específicas (TLS, redirects, pathType)
- Integrar com certificados (Cert-Manager ou Azure-managed)

### 4.4 Checklist Pré-AKS/Azure DevOps

- [ ] Substituir `secrets.local.yaml` por Secrets próprios do cluster/KeyVault
- [ ] Validar que o GitHub App está configurado com App ID, Installation ID e chave no ambiente gerenciado
- [ ] Confirmar que `PyJWT[crypto]` está instalado na imagem utilizada pelo pipeline
- [ ] Documentar nos valores do Helm a expectativa de variáveis (`GITHUB_APP_*`)

### 4.5 Segurança (Alta)

- Armazenamento seguro da chave privada
  - Não versionar a chave privada do GitHub App (não incluir PEM em `values.yaml` ou no repositório).
  - Em AKS, usar o mecanismo de Secrets do cluster ou Azure Key Vault. Exemplo (dev/local):

  ```bash
  kubectl create secret generic github-app-key \
   --from-file=private-key.pem=/path/to/private-key.pem \
   --namespace=seu-namespace
  ```

  - Garantir RBAC/ACLs restritos ao Secret e acesso apenas às ServiceAccounts necessárias.

- Minimizar permissões do GitHub App
  - Conceder apenas scopes estritamente necessários (por ex.: Issues read/write) e limitar a instalação a repositórios específicos — não usar "All repositories" se não for necessário.

- Dependências crypto e imagens de CI/runtime
  - Confirmar `PyJWT[crypto]` e `cryptography` em `backend/requirements.txt` e que a imagem Docker usada no pipeline contém essas dependências.
  - Evitar versões antigas/não suportadas do `cryptography` (siga políticas de segurança da base de imagens).

- Rotação e recuperação
  - Planejar rotação periódica da chave privada e o procedimento de deploy da nova chave (incluindo revogação da anterior no GitHub App se aplicável).
  - Documentar passo a passo para recuperação em caso de comprometimento.

- Auditoria e monitoramento
  - Logar eventos relevantes: geração de JWT, solicitações de token de instalação, chamadas de API significativas e falhas de autenticação.
  - Criar alertas para padrões anômalos (picos de geração de tokens, falhas repetidas, uso fora do horário esperado).

- Verificações rápidas recomendadas
  - Verificar `backend/requirements.txt` para `PyJWT[crypto]` e `cryptography`.
  - Escanear o repositório para arquivos PEM/strings que pareçam chaves privadas (evitar commits acidentais).
  - Incluir instruções de deploy seguro no Helm `values` docs (documentar que a chave deve vir de um Secret/KeyVault, não inline).

## 5. Frontend & API-First

### 5.1 Desacoplamento HTML (Média/Alta)

1. API-First mínima (endpoints JSON cobrindo dashboards)
2. Componentes React consumindo os novos endpoints
3. Remoção dos geradores HTML após paridade total

## 6. Backlog Futuro (Baixa)

### 6.1 Script de Preparação CSV

- Unificar script externo em utilitário interno e expor rota/fluxo integrado

### 6.2 Revisão de Colunas do CSV

- Mapear colunas realmente usadas
- Ajustar validação para tornar campos legados opcionais
- Atualizar documentação e testes de ingestão

### 7. Observações Finais

- Foco imediato: concluir documentação gerencial e iniciar o épico “AKS + Azure DevOps + Helm”
- Em paralelo, garantir que a migração GitHub App permaneça configurada em todos os ambientes (lembrar do Secret fora do repo)
