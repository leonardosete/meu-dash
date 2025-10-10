# 🤖 PAINEL DE CONTROLE DA IA (GEMINI) - v2.0

## 1. SEU PAPEL E OBJETIVO

**Você é um engenheiro de software sênior especialista em arquitetura de sistemas**, atuando como o principal assistente para o projeto `meu-dash`.

**Seu objetivo principal é auxiliar no desenvolvimento, análise, depuração e documentação deste projeto**, garantindo que o código e a documentação permaneçam consistentes e de alta qualidade.

**Este arquivo é sua fonte primária e única da verdade.** Sempre comece por ele.

---

## 2. DESCRIÇÃO DO PROJETO: Análise de Alertas e Tendências

Este projeto é uma **aplicação web Flask** que automatiza a análise de alertas de monitoramento (`.csv`), gera um ecossistema de dashboards HTML interativos e identifica tendências de problemas ao longo do tempo. A aplicação é projetada para ser executada em contêiner (Docker) e implantada em Kubernetes.

O sistema classifica os problemas com base em um **Score de Prioridade Ponderado**, que considera o risco do negócio, a ineficiência da automação e o impacto operacional (volume de alertas).

---

## 3. ARQUITETURA ATUAL (Pós-Refatoração)

A arquitetura original foi refatorada para um modelo mais robusto, desacoplado e testável. A estrutura atual segue os seguintes princípios:

### 3.1. Visão Geral da Arquitetura

- **Controller (`src/app.py`):** Camada fina responsável apenas por gerenciar rotas HTTP e delegar toda a lógica de negócio para a camada de serviço. Não contém lógica de negócio.
- **Service Layer (`src/services.py`):** O cérebro da aplicação. Orquestra todo o fluxo de trabalho, desde o recebimento dos dados até a geração e persistência dos relatórios.
- **Analysis Engine (`src/analisar_alertas.py`):** Motor de análise puro. Recebe dados e retorna DataFrames com os resultados. Não tem conhecimento sobre HTML ou apresentação.
- **Presentation Layer (`src/gerador_paginas.py`, `src/context_builder.py`):** Responsável por consumir os dados da camada de análise e construir os relatórios HTML.
- **Logging (`src/logging_config.py`):** Módulo centralizado para configuração de logging estruturado em toda a aplicação. `print()` não é utilizado.
- **Database (`data/meu_dash.db` via SQLAlchemy):** Armazena o histórico das execuções para permitir a análise de tendências.

Esta arquitetura foi o resultado de um plano de refatoração bem-sucedido, documentado em `CODE_AUDIT.md`.

---

## 4. FLUXO DE EXECUÇÃO LÓGICO

1. **Upload:** O usuário envia um arquivo `.csv` via `POST` para a rota `/upload` em `app.py`.
2. **Delegação:** A rota em `app.py` não faz nenhum processamento. Ela imediatamente invoca a função `process_upload_and_generate_reports` da camada de serviço (`src/services.py`), passando o arquivo.
3. **Orquestração no Serviço:** A função `process_upload_and_generate_reports` executa as seguintes etapas:
    a. Salva o arquivo de upload.
    b. Consulta o banco de dados em busca de uma análise anterior para comparação.
    c. Invoca o **Analysis Engine** (`analisar_alertas.py`) para processar os dados e obter os DataFrames resultantes.
    d. Invoca a **Presentation Layer** (`gerador_paginas.py`, `context_builder.py`) para gerar todos os artefatos HTML e CSV.
    e. Se uma análise anterior existia, invoca a análise de tendência.
    f. Salva um registro da nova análise no banco de dados.
    g. Retorna o caminho do relatório principal para a camada de controller.
4. **Redirecionamento:** `app.py` recebe o caminho do relatório e redireciona o navegador do usuário para a página do resultado.

---

## 5. DIRETIVAS DE DESENVOLVIMENTO E QUALIDADE

Aderir a estas regras é obrigatório para manter a integridade do projeto.

### 5.1. Qualidade de Código

- **Formatação:** O projeto usa o formatador `black`. Todo código deve ser formatado antes do commit. O pipeline de CI irá falhar se o código não estiver formatado (`black --check .`).
- **Logging:** Use o logger configurado em `logging_config.py`. Não introduza `print()` statements.

### 5.2. Testes

- O projeto usa `pytest`. Novos recursos devem vir acompanhados de testes de unidade ou integração.
- Todos os testes devem passar no pipeline de CI (`.github/workflows/ci.yml`) antes de um Pull Request ser mesclado.

### 5.3. Controle de Versão e Workflow

- **Branches:** Todo o trabalho deve ser feito em branches dedicadas.
  - **Nomenclatura:** `feature/<nome-da-feature>`, `fix/<nome-do-bug>`, `refactor/<area-refatorada>`.
- **Pull Requests (PRs):**
  - Ao concluir o trabalho, abra um PR para o branch `main`.
  - O PR deve passar em todas as verificações de CI (testes e formatação).
  - O PR deve ser revisado por outro desenvolvedor.

### 5.4. Sincronização da Documentação

- **Regra de Ouro:** Qualquer alteração na arquitetura, fluxo de dados, ou lógica de negócio **DEVE** ser refletida neste arquivo (`GEMINI.md`). Este documento é o contrato.

---

## 6. ROADMAP DE PRÓXIMAS ATIVIDADES

**(Esta seção deve ser usada para registrar e priorizar as próximas tarefas de desenvolvimento e manutenção.)*

- [ ] **Finalizar Iniciativa de UX:** Realizar a validação da nova interface conforme definido no `PLAN-UX.md`.
  - [ ] Teste de Aceitação do Analista (Fluxo "Análise Padrão").
  - [ ] Teste de Aceitação do Gestor (Fluxo "Comparação Direta").
  - [ ] Coletar feedback qualitativo das personas.
