<!-- .github/copilot-instructions.md - orientações para agentes AI que trabalham neste repositório -->
# Instruções rápidas para Copilot / agentes AI — smart-remedy
Idioma padrão: PT-BR
Público-alvo: agentes automatizados (estilo Copilot) que vão criar, modificar ou revisar código neste repositório.

Mantenha isto curto e acionável. Se precisar de contexto mais amplo, consulte `README.md` e `ARCHITECTURE.md`.

1) Visão geral (uma linha cada)
  - Projeto desacoplado: `backend/` (API Flask, motores de análise) + `frontend/` (SPA React com Vite).
  - CI/CD-First: o pipeline valida, testa, constrói e publica artefatos — evitar dependência em `docker-compose` local.
  - Fluxo de dados: usuário envia CSV -> módulos de análise do backend transformam Alertas -> agrupam em Casos -> geram relatórios HTML estáticos.

2) O que alterar e onde (tarefas comuns)
  - Lógica de análise (backend): edite módulos em `backend/src/` (ex.: `analisar_alertas.py`, `analise_tendencia.py`, `gerador_paginas.py`). Mantenha o processamento de dados nos motores de análise; os controllers em `app.py` devem ser finos.
  - API: `backend/src/app.py` expõe rotas e contratos JSON. Ao alterar um endpoint, atualize os testes em `backend/tests/` e, se aplicável, os ADRs em `docs/adrs/`.
  - Frontend: edite componentes em `frontend/src/components/` e chamadas de API em `frontend/src/services/api.ts`. O frontend consome JSON da API — não adicione renderização server-side.

3) Testes / validação local (como a equipe espera que você valide alterações)
  - Fluxo CI-First: os testes automatizados (unit, integração e E2E) são executados no pipeline de CI. Confie no CI para a validação final.
  - Validação local: restrinja a validação local às verificações rápidas e de estilo (format/lint) para evitar ciclos de feedback longos e diferenças de ambiente. Use estes alvos quando fizer mudanças que afetam apenas formatação ou lint:
    - `make install-backend` — instala dependências do backend e cria `.venv` (dev local).
    - `make install-frontend` — instala dependências do frontend.
    - `make format` — formata automaticamente o código (use antes de commitar).
    - `make check` — executa formatação/lint/checagens rápidas (espelha parte do CI).
  - Observação: o `Makefile.mk` inclui alvos que aplicam correções automaticamente (`make format`, `make lint`). Execute-os como parte do fluxo local para reduzir commits de correção que só aparecem após falhas no CI.
  - Observação sobre testes locais: se precisar rodar a suíte de testes localmente, execute-os a partir do diretório `backend` (ou configure `PYTHONPATH`) para evitar erros de import como `ModuleNotFoundError: No module named 'src'`. Porém - repita: a fonte de verdade é o CI.
  - Frontend local (desenvolvimento apenas):
    - `cd frontend && npm run dev` (Vite) para rodar a SPA localmente.
    - `npm run build` e `npm run test` (`vitest`) para validações locais ocasionais; o CI é o responsável pela verificação definitiva.

4) Convenções e padrões importantes
  - CI/CD-First: não adicione fluxos `docker-compose` locais permanentes. Se criar helpers locais, documente-os em `CONTRIBUTING.md` e prefira scripts opt-in.
  - Responsabilidade única: motores de análise calculam scores e moldam DataFrames; a geração de páginas é uma etapa separada que produz artefatos HTML estáticos.
  - Banco de dados: a migração para **PostgreSQL** já foi concluída e é o modelo definitivo de produção. Não adicione código dependente somente de SQLite. Use drivers compatíveis (o `requirements.txt` já inclui `psycopg2-binary`).
  - Backend Application Factory: `backend/src/app.py` utiliza o padrão Application Factory (chamada `create_app()` e, normalmente, `app = create_app()` é exposto). Ao adicionar extensões ou escrever testes, mantenha compatibilidade com esse padrão.
  - Schema CSV é rígido: consumidores assumem nomes exatos de colunas (veja `README.md` — "Formato do Arquivo de Entrada"). Ao alterar nomes de colunas, atualize o README e implemente compatibilidade/migração.
  - Segredos: nunca codifique segredos no repositório. Use Kubernetes Secrets (veja `CONTRIBUTING.md` sobre `admin-token-secret`).

5) Pontos de integração e infra
  - Manifests Kubernetes e instruções de deploy ficam na raiz (`kubernetes.yaml`, `kubernetes/`) e há também um manifesto `kubernetes-v3.yaml` com sidecar/Ingress usado para deploys mais recentes. O deploy espera imagens construídas e publicadas pelo CI.
  - Nome da imagem oficial: a aplicação é publicada como `sevenleo/smart-remedy` (nome da app: `smart-remedy`). Use esta nomenclatura ao referenciar imagens ou atualizar manifests.
  - O pipeline de CI constrói e publica imagens Docker; builds locais não são fonte de verdade para produção.

6) Exemplos de edições acionáveis (mensagens de commit/PR sugeridas)
  - "Fix: tolerar ausência da coluna CSV opcional `metric_name` em `backend/src/analisar_alertas.py` e atualizar exemplo do schema no README. Adicionado teste unitário para coluna ausente."
  - "Feat: expor `/api/v1/report/:id` metadata (backend/src/app.py) e adicionar chamada cliente em `frontend/src/services/api.ts`. Testes atualizados em `backend/tests/test_api.py`."

7) Arquivos para consultar ao raciocinar
  - `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md` — filosofia do projeto e fluxos de desenvolvimento
  - `Makefile.mk` (invocado via `Makefile`) — alvos úteis para validação local
  - `backend/src/*` e `backend/tests/*` — lógica do backend e testes
  - `frontend/src/*` e `frontend/package.json` — pontos de entrada e scripts do frontend

8) O que *não* fazer
  - Não adicionar ou depender de fluxos `docker-compose` locais não documentados. O repositório adota explicitamente CI/CD-First.
  - Não commitar segredos nem tokens de serviço.

9) Se o comportamento for ambíguo
  - Siga os testes existentes e as checagens do CI. Se for necessária uma decisão de design, crie um ADR curto em `docs/adrs/` explicando a razão.

10) Quando perguntar ao humano
  - Ao mudar contratos públicos da API (adicione um ADR e solicite revisão).
  - Ao adicionar novo armazenamento persistente ou fluxos que envolvam segredos.

PR checklist (sugestão rápida)
  - Rode `make format` e `make check` localmente (formatação/lint) antes de abrir o PR.
  - Não altere nomes de imagem/container; use `sevenleo/smart-remedy` se precisar referenciar a imagem oficial.
  - Confirme que nenhuma credencial foi adicionada ao commit (use `git diff --staged`).
  - Se alterar a inicialização do app, mantenha compatibilidade com `create_app()` em `backend/src/app.py`.
  - Inclua ou atualize testes relevantes em `backend/tests/` e garanta que o objetivo do PR esteja descrito no título e descrição.

Fim — peça feedback dos mantenedores se alguma seção estiver incompleta ou exigir exemplos concretos.
