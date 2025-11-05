## Mecanismo de Feedback de Usuário — Análise Inicial

Data: 2025-11-03

Resumo
------

Este documento descreve opções de implementação, desafios, riscos e passos recomendados para introduzir um mecanismo de feedback direto dos usuários na aplicação.

1) Objetivo / contrato mínimo

- Campos mínimos do payload:
  - type: "bug" | "feature" | "suggestion" | "other"
  - message: string (obrigatório)
  - context: optional string (ex: nome do CSV, id do relatório, rota, timestamp)
  - contact_email: optional string (opt-in)
  - anonymous: boolean (opt-in)
  - tags: optional array[string]

2) Opções de arquitetura (prós/cons)

- Persistir em banco de dados interno (Postgres)
  - Prós: histórico completo, consultas e relatório internos, integração com triagem; controle total.
  - Contras: necessidade de modelagem, migração, UI de administração, custo operacional.

- Enfileirar em sistema externo / ticketing (ex: create GitHub Issue, forward to Slack, send email)
  - Prós: rapidez de implementação, integração com processos existentes (triagem via issues), sem necessidade de infra adicional.
  - Contras: dependência externa, menos controle sobre dados, necessidade de tokens/credentials, risco de vazamento de dados sensíveis se não filtrado.

- Enviar a um serviço de terceiros (Typeform, Intercom, Sentry custom) via webhook
  - Prós: UX pronta, filtragem/analytics embutidos.
  - Contras: custo, vendor lock-in, compliance/privacidade.

3) Desafios e preocupações importantes

- Privacidade / Dados Pessoais
  - Feedback pode conter PII (screenshots, nomes, trechos do CSV). Necessário definir redaction rules e um mecanismo para avisar/consentir o usuário.

- Spam e abuso
  - Necessário rate-limiting, CAPTCHA opcional e validação/normalização de conteúdo para evitar flood.

- Moderação e triagem
  - Definir um fluxo de triagem: automatic tagging (ex: prioritizar 'bug') + roteamento (Slack channel, e-mail, criar issue automaticamente). Possibilidade de criar painel simples para operadores.

- Segurança / Exfiltração
  - Proteger endpoints com CSRF, validação do payload; evitar que uploads arbitrários (screenshots) sejam aceitos sem scanning/limitação.

- Localização / Idioma
  - Se base de usuários multilíngue, prover campo de idioma ou detectar automaticamente; priorizar mensagens em pt-BR inicialmente.

4) Requisitos técnicos mínimos (MVP)

- Backend: novo endpoint POST /api/v1/feedback
  - Validate payload, strip/normalize content, persist to `feedback` table or forward to triage (ex: GitHub issue via token) depending on chosen option.

- DB schema (MVP): feedback(id, type, message, context, anonymous, contact_email, created_at, processed_at, status, source)

- Frontend: pequeno modal/form em SPA (React) com fields: type, message, optional contact_email, optional context autofill.

- Admin/triage: webhook to Slack or create GitHub issue for first iteration; dashboard optional later.

5) Plano de implementação recomendado (curto prazo)

- Fase 0 (Design rápido): definir contrato e exemplos de payload (1 day)
- Fase 1 (MVP rápido): implementar POST endpoint que cria uma GitHub Issue (or send to Slack) — evita necessidade de DB e UI de admin (2-3 days)
- Fase 2: Persistência em Postgres + painel de triagem básico (web) + proteção (rate-limit, CAPTCHA) (3-5 days)
- Fase 3: aprimorar com ML/Triagem automática, tags, relatórios e integrações (opcional)

6) Estimativa de esforço (grosso)

- MVP (Fase 0 + Fase 1): 2–4 dias de esforço de desenvolvimento (backend + pequena UI + infra de webhook). Requer token para GitHub or Slack.
- Persistência + painel: +3–5 dias.

7) Riscos e mitigação

- Risco: vazamento de dados sensíveis no feedback (screenshots/textos com PII).
  - Mitigação: aviso de consentimento no formulário; validação automática e remover attachments; opção de anonimato.

- Risco: flood/spam.
  - Mitigação: rate-limit por IP/user, CAPTCHA, e e-mail opt-in verification.

8) Próximos passos imediatos (recomendado)

- Confirmar que o mantenedor aprova o contrato mínimo (campos e anonimato).
- Decidir destino inicial do feedback (GitHub Issue vs Slack vs DB).
- Eu posso: 1) criar o endpoint backend mínimo + rota, e 2) adicionar um modal simples no frontend para envio — ou, se preferir, primeiro só encaminhar para Slack/GitHub para validar o fluxo com o mínimo de infra.

---

Registro: este documento foi criado automaticamente como resultado da priorização solicitada em `REFACTOR_PLAN.md` (2025-11-03). Atualizar conforme decisões e feedback do time.
