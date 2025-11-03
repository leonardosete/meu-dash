# ✅ Plano de Ação: Roadmap Prioritário (Seção Atual)

**Nota:** O conteúdo histórico (seções 1–4 e histórico da Fase 3) foi movido para `OLD_REFACTOR_PLAN.md` para manter este arquivo focado nas prioridades atuais. Consulte `OLD_REFACTOR_PLAN.md` para o histórico completo.

---

## 0. Prioridade Imediata: Mecanismo de Feedback de Usuário

Objetivo: permitir que usuários (mantedores e utilizadores da ferramenta) enviem feedback direto sobre a aplicação através de GitHub Issues — sugestões de melhoria, solicitações de novas features, reports de bugs e pedidos de remoção de funcionalidades — de forma simples, audível e moderável.

Por que é prioritário: feedback direto de usuários guiará decisões de produto e permitirá priorizar correções/itens de valor real antes de grandes mudanças infra-estruturais. Além disso, ajuda a reduzir ruído de requisições internas e fornece evidências qualitativas sobre impacto das alterações.

Decisão de Arquitetura: após análise em `docs/FEEDBACK_PLAN.md`, decidiu-se usar GitHub Issues como backend de persistência devido aos benefícios imediatos (triagem via labels, discussões threaded, notificações) sem necessidade de infra adicional.

Tarefas de Implementação:

- [ ] Criar token do GitHub com permissão de criação de issues (escopo mínimo necessário).
- [ ] Implementar endpoint backend (POST /api/v1/feedback) que use GitHub REST API para criar issues:
  - Campos: tipo (label), título, descrição, email (opcional), contexto.
  - Validação de payload e rate limiting básico.
  - Retornar link da issue criada na resposta.
- [ ] Criar componente React para o modal de feedback:
  - Botão discreto que abre o modal.
  - Campos essenciais com validação.
  - Preview do conteúdo antes de enviar.
  - Confirmação com link para a issue criada.
- [ ] Configurar labels e templates de issue no repositório:
  - Labels para tipos de feedback (bug, feature, etc.).
  - Template básico para padronizar o formato.
  - Documentar processo de triagem no README.

Ligação: ver `docs/FEEDBACK_PLAN.md` para análise completa e detalhes da decisão de usar GitHub Issues.


---

## 5. Novas Prioridades e Roadmap (decisão do mantenedor)

O mantenedor decidiu priorizar uma transição para um ambiente de produção baseado em AKS (Azure Kubernetes Service), pipelines no Azure DevOps e empacotamento com Helm. Abaixo estão as tarefas consolidadas, com prioridades e passos acionáveis. Mantivemos o histórico anterior intacto — esta seção documenta o que falta entregar segundo as decisões mais recentes.

Prioridade Alta

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

Prioridade Média/Alta

- [ ] Desacoplar totalmente a geração de HTML do backend (mover para API-First)
  - Justificativa: reduzir acoplamento e permitir que o frontend seja responsável pela renderização, além de permitir consumo por outras ferramentas.
  - Plano de Ação (sugestão de fases):
    1. **API-First mínima:** adicionar endpoints JSON que sirvam os dados necessários para gerar os dashboards principais (KPIs, listas, trend summaries). Não remover ainda a geração de HTML; oferecer ambas durante migração.
    2. **Frontend/Renderer:** criar novos componentes React que consumam os endpoints e renderizem os dashboards (substituir `<iframe>`s progressivamente).
    3. **Limpeza:** quando cobertura e parity funcional forem confirmadas, remover geradores HTML e templates backend usados apenas para visualização.
  - Observação: alguns artefatos (textos conceituais, explicações, guias) podem precisar ser portados para conteúdo dinâmico (CMS leve ou arquivos markdown servidos pelo frontend).

Prioridade Média

- [ ] Atualizar `doc_gerencial.html` (documentação gerencial)
  - Justificativa: o conteúdo atual ainda não expressa a mensagem desejada ao público gerencial; será a etapa final de polimento.
  - Plano de Ação:
    - [ ] Rescrever seções chave (Desafio, Proposta de Valor, Como Usar) para foco em benefícios mensuráveis.
    - [ ] Atualizar exemplos e capturas de tela para refletir a UI atual.
    - [ ] Aprovação final com stakeholder antes de publicar.

Prioridade Baixa (posterior)

- [ ] Unificar script externo de preparação de CSV na aplicação
  - Justificativa: atualmente existe um script Python externo que prepara o CSV de entrada; unificá-lo permitirá um fluxo integrado e reduzirá passos manuais.
  - Plano de Ação:
    - [ ] Analisar o script externo e suas dependências; criar um módulo reutilizável no `backend/src/utils` (ex: `preparer.py`).
    - [ ] Expor uma rota que execute a preparação (ou integrar ao pipeline de upload) e gerar o CSV que o pipeline de análise consome.
    - [ ] Atualizar testes e documentação para refletir o novo fluxo.

Observação final

Estas novas prioridades refletem a decisão estratégica de mover para AKS/Azure e empacotar com Helm, além de priorizar a separação da apresentação (frontend) e lógica (backend). Sugiro que a equipe trate o bloco "AKS + Azure DevOps + Helm" como o próximo epic de entrega (Prioridade Alta) e que as tarefas de desacoplamento (API-First) sejam a penúltima etapa antes da limpeza final da documentação gerencial.
