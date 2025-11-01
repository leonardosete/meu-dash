# ✅ Plano de Ação: Fase 3 - Finalização e Limpeza

**Última Atualização:** 2025-10-28
**Arquiteto de Refatoração:** Gemini Code Assist

## 1. Resumo do Estado Atual

A refatoração principal para uma arquitetura desacoplada (API Flask + SPA React) foi concluída. O projeto está na **Fase 3: Finalização e Limpeza**, com foco em robustecer a segurança, a lógica de negócio e a documentação.

As fases 0, 1 e 2 estão arquivadas e foram removidas deste plano para maior clareza.

---

## 2. Tarefas Pendentes por Prioridade

### Prioridade 0: Crítico / Estrutural

#### [x] 🚀 Unificar Workflow de Desenvolvimento para CI/CD-first

- **Justificativa:** Eliminar a dependência do `docker-compose` para o desenvolvimento local e adotar um fluxo de trabalho único, baseado em Git e CI/CD, que espelha o ambiente de produção. Isso reduz a deriva de ambiente ("funciona na minha máquina"), simplifica o onboarding e garante que todo o desenvolvimento seja feito contra uma arquitetura consistente.
- **Plano de Ação:**
  - [x] Remover todos os artefatos de desenvolvimento local baseados em `docker-compose` (ex: `docker-compose.yml`, `Dockerfile.dev`).
  - [x] Remover os comandos obsoletos do `Makefile.mk` que dependiam do `docker-compose`.
  - [x] Reescrever a documentação de contribuição (`CONTRIBUTING.md`) e o `README.md` para refletir o novo fluxo de trabalho: `codificar -> push -> CI/CD -> validar em K8s`.
  - [x] Garantir que o pipeline de CI (`.github/workflows/ci.yml`) esteja completo, com testes e build da imagem de produção.

#### [ ] 🚀 Migrar Banco de Dados de SQLite para PostgreSQL

- **Justificativa:** O SQLite é um banco de dados de arquivo único e representa o principal **Ponto Único de Falha (SPOF)** da arquitetura. Ele impede a escalabilidade horizontal (múltiplas réplicas) e não é adequado para um ambiente de produção em Kubernetes. A migração para PostgreSQL é um pré-requisito para alta disponibilidade e resiliência.
- **Plano de Ação:**
  - [ ] Migrar a aplicação de SQLite para um banco de dados compatível com múltiplas réplicas (PostgreSQL), um pré-requisito para a escalabilidade real em Kubernetes.

---

### Prioridade 1: Crítico / Alto

#### [ ] 🧠 Validar e Refinar Lógica de Análise de Scoring

- **Justificativa:** A principal funcionalidade de negócio (cálculo do `score_ponderado_final`) passou por múltiplas refatorações. É crucial garantir que o resultado final esteja 100% correto e alinhado com as regras de negócio.
- **Plano de Ação:**
  - [x] **Revisão de Código:** Analisar detalhadamente os scripts `analisar_alertas.py` e `analise_tendencia.py` em busca de "code smells", inconsistências ou bugs na lógica de cálculo.
  - [x] **Melhorar Docstrings:** Garantir que todas as funções críticas em `analisar_alertas.py` tenham docstrings claras.
  - [x] **Validação de Integração E2E (Geral):** Realizar um teste de ponta a ponta com um arquivo CSV complexo para validar a integração do sistema.
  - [x] **Validação de Regressão (Cenários Específicos):** Executar testes E2E com múltiplos arquivos CSV, cada um focado em uma regra de negócio específica.
    - [x] Cenário: Instabilidade Crônica
    - [x] Cenário: Sucesso Parcial (Closed Skipped, Canceled)
    - [x] Cenário: Falha Persistente
    - [x] Cenário: Sucesso Estabilizado
  - [ ] **Validação de Negócio (Golden File):** Validar o resultado da análise de um arquivo CSV de produção contra o resultado esperado, definido pelo especialista de negócio.

---

### Prioridade 2: Alto

#### [ ] 📄 Revisar e Atualizar Documentação Gerencial (`doc_gerencial.html`)

- **Justificativa:** Este documento é a "página de venda" da ferramenta para stakeholders. Ele precisa refletir com precisão a inteligência e o valor da versão atual do sistema.
- **Plano de Ação:**
  - [ ] Reestruturar a seção "Classificação da Análise" para incluir o 4º pilar: "Pontos de Atenção".
  - [ ] Revisar e refinar a explicação do "Score Ponderado" para incluir o `fator_ineficiencia_task` e os novos status (`Canceled`, `Closed Skipped`).
  - [ ] Garantir que a linguagem seja clara, focada em valor de negócio e que todos os exemplos estejam alinhados com a lógica atual.
  - [ ] Refinar o conteúdo a partir da seção "Usando o Dashboard para Decisões" em diante, garantindo clareza e precisão.

#### [ ] 💬 Revisar Mensagens do "Diagnóstico Rápido"

- **Justificativa:** As mensagens do "Diagnóstico Rápido" são a primeira e mais importante interpretação da ferramenta para o usuário. Elas precisam ser 100% coerentes com a lógica de negócio e claras para o gestor.
- **Plano de Ação:**
  - [ ] Revisar cada um dos cenários de diagnóstico (`_determine_verdict` em `analise_tendencia.py`).
  - [ ] Garantir que a linguagem seja precisa, concisa e transmita o insight correto.
  - [ ] Verificar se os emojis e a classe CSS (`highlight-success`, `highlight-danger`, etc.) estão alinhados com a mensagem.

### Prioridade 3: Médio

#### [ ] 🚀 Finalizar Pipeline de CI/CD

- **Justificativa:** O pipeline atual (`.github/workflows/ci.yml`) já valida o backend e o frontend, mas não constrói a imagem Docker de produção final, criando um processo de deploy manual.
- **Plano de Ação:**
  - [ ] **Modificar Build do Docker:** Alterar a etapa de build para usar o `Dockerfile` multi-estágio de produção, que constrói o frontend e o backend em uma única imagem.
  - [ ] **Publicar Imagem:** Garantir que a imagem final seja publicada no Docker Hub (ou outro registry) com as tags corretas.

#### [ ] 📚 Revisar e Atualizar Documentação para o Usuário Final (Seção "Conceitos")

- **Justificativa:** A seção "Conceitos" no dashboard (`resumo_geral.html`) serve como a documentação "viva" para o usuário. Ela precisa refletir 100% a lógica de negócio final e estável.
- **Plano de Ação:**
  - [ ] Revisar todas as tabelas de pesos e multiplicadores em `gerador_html.py` para garantir que correspondam aos valores em `constants.py`.
  - [ ] Ajustar os textos e exemplos para que sejam claros, simples e precisos.

### Prioridade 4: Baixo (Melhoria de UX)

#### [ ] ✨ Ajuste de UX: Trocar Ícone do Card "Pontos de Atenção"

- **Justificativa:** O ícone atual '⚠️' pode ser confundido com "Instabilidade Crônica". Um ícone de ferramenta '🛠️' comunicaria melhor a ideia de "automação que precisa de ajuste".
- **Plano de Ação:**
  - [ ] Modificar o `gerador_html.py` para substituir o ícone no card de "Pontos de Atenção".

---

## 3. Tarefas Concluídas (Histórico da Fase 3)

A lista abaixo resume as principais tarefas que já foram concluídas nesta fase, conforme registrado no `DIARIO_DE_BORDO.md`.

### [x] ️ Implementar Validação de Schema de Entrada (Porteiro de Dados)

- **Resultado:** A função `carregar_dados` agora valida estritamente o schema do CSV na entrada, rejeitando arquivos inválidos e garantindo a integridade dos dados.

#### [x] 🔐 Proteger Todos os Endpoints da API com Autenticação

- **Resultado:** Todos os endpoints que disparam ações (`upload`, `compare`, `delete`) foram protegidos com o decorador `@token_required`. A UI foi ajustada para refletir o estado de autenticação.

#### [x] 📚 Criar Documentação da API com Flasgger

- **Resultado:** Todos os endpoints da API foram documentados com Flasgger, gerando uma UI do Swagger (`/apidocs`) interativa. O `README.md` foi atualizado para apontar para esta nova documentação.

#### [x] 🧹 Limpeza e Organização da Documentação

- **Resultado:** O `ARCHITECTURE.md` foi atualizado, links quebrados no `README.md` e `CONTRIBUTING.md` foram corrigidos, e foi criado o `guia.md` para centralizar a navegação.

#### [x] 🐞 Correções de Bugs e Refatorações Diversas

- **Resultado:** Resolvidos inúmeros bugs e débitos técnicos identificados pelo SonarQube e durante a depuração, incluindo: problemas de I/O no Docker, links de retorno quebrados nos relatórios, bugs de interatividade e reatividade na UI, entre outros.

#### [x] 🔬 Robustecer e Organizar Testes do Backend

- **Justificativa:** Os testes são nossa rede de segurança. Eles precisam estar bem organizados e cobrir toda a lógica de negócio para permitir futuras refatorações com confiança.
- **Plano de Ação:**
  - [x] **Refatorar Estrutura:** Mover a configuração do Pytest do `pyproject.toml` da raiz para um novo arquivo `backend/pyproject.toml`, isolando o ambiente de teste.
  - [x] **Revisar Cobertura:** Analisar os testes existentes (ex: `test_analise_scoring.py`) para garantir que eles validam os cenários corretos da lógica de scoring.
  - [x] **Separar Responsabilidades:** Garantir que não haja "lixo" de teste no código da aplicação e que os testes estejam focados em validar uma única funcionalidade por vez.
- **Resultado:** A estrutura de testes foi isolada, o `Makefile.mk` foi corrigido, e os testes de scoring foram refatorados para maior cobertura e clareza. Bugs na lógica de negócio foram encontrados e corrigidos graças a essa robustez.

#### [x] ⚙️ Consolidar Ferramentas de Qualidade

- **Resultado:** A configuração da ferramenta `black` foi removida do `pyproject.toml`, padronizando o uso do `Ruff` para formatação e linting.

---

## 4. Decisões Estratégicas e Débitos Técnicos Conhecidos

- **Geração de HTML no Backend:** Decidimos **manter** a lógica de geração de relatórios HTML no backend por enquanto. A tarefa "Remover Código Morto" (`templates/`) foi reavaliada e está incorreta, pois este código está em uso. A migração dessa lógica para o frontend é uma refatoração futura, a ser planejada em uma "Fase 4".

---

## 🚀 Plano de Ação: Fase 4 - Evolução e Novas Features (Backlog)

### Prioridade Alta

#### [ ] 🧠 Implementar Persistência de Estado para Remediação Manual

- **Justificativa:** Atualmente, a análise é "stateless". Para evitar que a equipe precise reavaliar manualmente o mesmo caso a cada nova análise, é necessário um mecanismo para persistir a decisão de `manual_remediation_expected`.
- **Plano de Ação:**
  - [ ] **Definir Arquitetura:** Criar um ADR (Architecture Decision Record) para decidir a melhor abordagem de persistência (ex: banco de dados SQLite, arquivo de estado JSON).
  - [ ] **Implementar Lógica de Persistência:** Adicionar a lógica no backend para salvar e consultar o estado de um caso.
  - [ ] **Ajustar Geração de Relatórios:** Modificar o `analisar_alertas.py` para considerar o estado persistido ao gerar o `atuar.csv`.
  - [ ] **Ajustar UI (se necessário):** Avaliar se a interface do frontend precisa de alguma modificação para suportar este fluxo.
