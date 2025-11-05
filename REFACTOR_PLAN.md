# ✅ Plano de Ação: Roadmap Prioritário (Seção Atual)

**Nota:** O conteúdo histórico (seções 1–4 e histórico da Fase 3) foi movido para `OLD_REFACTOR_PLAN.md` para manter este arquivo focado nas prioridades atuais. Consulte `OLD_REFACTOR_PLAN.md` para o histórico completo.

---

## ✅ 0. Prioridade Imediata: Mecanismo de Feedback de Usuário

**STATUS: CONCLUÍDO** ✅

Objetivo: permitir que usuários (mantedores e utilizadores da ferramenta) enviem feedback direto sobre a aplicação através de GitHub Issues — sugestões de melhoria, solicitações de novas features, reports de bugs e pedidos de remoção de funcionalidades — de forma simples, audível e moderável.

### ✅ **Implementação Completa**

- ✅ Endpoint backend (`POST /api/v1/feedback`) com validação e GitHub API integration
- ✅ Componente React `FeedbackModal` com formulário e preview
- ✅ Tipos TypeScript (`FeedbackData`) definidos
- ✅ Testes backend completos (5 cenários de teste)
- ✅ Labels do GitHub configuradas (bug, feature, other, suggestion)
- ✅ Issues de teste criadas e validadas com labels corretas
- ✅ Documentação técnica em `docs/FEEDBACK_PLAN.md`
- ✅ README atualizado com menção ao sistema de feedback
- ✅ Token do GitHub criado e funcional

### 🎯 **Resultado**

Sistema totalmente funcional permite que usuários enviem feedback diretamente pela interface, criando automaticamente issues estruturadas no GitHub com templates específicos e labels apropriadas.

---

## 5. Novas Prioridades e Roadmap (decisão do mantenedor)

O mantenedor decidiu priorizar uma transição para um ambiente de produção baseado em AKS (Azure Kubernetes Service), pipelines no Azure DevOps e empacotamento com Helm. Abaixo estão as tarefas consolidadas, com prioridades e passos acionáveis. Mantivemos o histórico anterior intacto — esta seção documenta o que falta entregar segundo as decisões mais recentes.

Prioridade Alta

- [ ] Refinar detecção de "Instabilidade Crônica" no backend (urgente)
  - Justificativa: a regra atual considera apenas volume (≥5 alertas) e pode classificar incorretamente casos de sucesso parcial como instabilidade; precisamos adicionar janela temporal curta e contar somente execuções `Closed`.
  - Plano de Ação:
    - [ ] Definir constante global `JANELA_INSTABILIDADE_HORAS` no backend para parametrizar a janela temporal (inicialmente 2 horas).
    - [ ] Atualizar a árvore de decisão em `backend/src/analisar_alertas.py` para exigir simultaneamente: `last_tasks_status == "Closed"`, pelo menos 5 execuções `Closed` e diferença `last_event - first_event` dentro da janela configurável.
    - [ ] Ajustar testes unitários para cobrir cenários dentro/fora da janela e validar a nova regra.
    - [ ] Revisar relatórios para garantir que a categoria reflita apenas casos realmente recorrentes em curto intervalo.
- [ ] Migrar infra/CI para AKS + Azure DevOps + Helm
  - Justificativa: ambiente de produção alvo será AKS; pipelines e registry serão do Azure (não usaremos Docker Hub). Isto exige atualização do processo de build/publish e dos manifests para Helm charts.
  - Plano de Ação:
    - [ ] Criar Helm chart (chart base) para a aplicação (`charts/smart-remedy`) que contenha templates para Deployment, Service, Ingress, ConfigMap e Secrets (valores parametrizáveis).
    - [ ] Converter `kubernetes-v3.yaml` em chart/values e mover privilégios sensíveis para valores externos (SecretScope no Azure).
    - [ ] Criar pipeline de CI/CD no Azure DevOps (yaml) que: build da imagem, push para Azure Container Registry (ACR), package do chart com tag apropriada e/publicação do chart (opcional) ou atualização do repositório GitOps.
    - [ ] Atualizar registros e documentação de deploy para apontar para ACR e Azure DevOps. Validar autenticação e permissões (Service Principal/Managed Identity).
    - [ ] Testar deploy em ambiente de stage AKS com Helm (helm upgrade --install) e validar probes/healthchecks.

Prioridade Alta (parte de infraestrutura)

- [ ] Ajustar configuração de Ingress e rede para AKS
  - Justificativa: o Ingress atual pode precisar de adaptação para o controlador usado no AKS (NGINX Ingress Controller, Application Gateway Ingress Controller, etc.) e políticas de TLS/HTTPS específicas do cloud.
  - Plano de Ação:
    - [ ] Identificar qual Ingress Controller será usado em AKS (recomendar NGINX ou AGIC conforme infra).
    - [ ] Converter regras de Ingress do chart para suportar anotações específicas do controller (TLS, redirect, HSTS, rewrites, pathType).
    - [ ] Validar integração com certificação (KeyVault/Cert Manager ou Azure-managed certs).

Prioridade Alta (deploy/registry)

- [ ] Ajustar pipeline e registry — ACR + autenticação
  - Plano de Ação:
    - [ ] Substituir etapa de push para Docker Hub por push para Azure Container Registry (ACR) no pipeline.
    - [ ] Configurar service connection no Azure DevOps (Service Principal) com permissões de push/pull no ACR.
    - [ ] Garantir que imagens geradas usem tags semânticas e as mesmas tags sejam referenciadas pelos charts/values.

Prioridade Alta (documentação)

- [ ] Atualizar `doc_gerencial.html` (documentação gerencial) - **ATUAR AGORA**
  - Justificativa: o conteúdo atual ainda não expressa a mensagem desejada ao público gerencial; vamos atuar nela agora antes de continuar outros desenvolvimentos.
  - Plano de Ação:
    - [ ] Rescrever seções chave (Desafio, Proposta de Valor, Como Usar) para foco em benefícios mensuráveis.
    - [ ] Atualizar exemplos e capturas de tela para refletir a UI atual.
    - [ ] Aprovação final com stakeholder antes de publicar.

Prioridade Média/Alta

- [ ] Desacoplar totalmente a geração de HTML do backend (mover para API-First)
  - Justificativa: reduzir acoplamento e permitir que o frontend seja responsável pela renderização, além de permitir consumo por outras ferramentas.
  - Plano de Ação (sugestão de fases):
    1. **API-First mínima:** adicionar endpoints JSON que sirvam os dados necessários para gerar os dashboards principais (KPIs, listas, trend summaries). Não remover ainda a geração de HTML; oferecer ambas durante migração.
    2. **Frontend/Renderer:** criar novos componentes React que consumam os endpoints e renderizem os dashboards (substituir `<iframe>`s progressivamente).
    3. **Limpeza:** quando cobertura e parity funcional forem confirmadas, remover geradores HTML e templates backend usados apenas para visualização.
  - Observação: alguns artefatos (textos conceituais, explicações, guias) podem precisar ser portados para conteúdo dinâmico (CMS leve ou arquivos markdown servidos pelo frontend).

Prioridade Baixa (posterior)

- [ ] Unificar script externo de preparação de CSV na aplicação
  - Justificativa: atualmente existe um script Python externo que prepara o CSV de entrada; unificá-lo permitirá um fluxo integrado e reduzirá passos manuais.
  - Plano de Ação:
    - [ ] Analisar o script externo e suas dependências; criar um módulo reutilizável no `backend/src/utils` (ex: `preparer.py`).
    - [ ] Expor uma rota que execute a preparação (ou integrar ao pipeline de upload) e gerar o CSV que o pipeline de análise consome.
    - [ ] Atualizar testes e documentação para refletir o novo fluxo.

Observação final

Estas novas prioridades refletem a decisão estratégica de mover para AKS/Azure e empacotar com Helm, além de priorizar a separação da apresentação (frontend) e lógica (backend). Sugiro que a equipe trate o bloco "AKS + Azure DevOps + Helm" como o próximo epic de entrega (Prioridade Alta) e que as tarefas de desacoplamento (API-First) sejam a penúltima etapa antes da limpeza final da documentação gerencial.
