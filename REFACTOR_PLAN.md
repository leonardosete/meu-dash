# ✅ Plano de Ação: Fase 3 - Finalização e Limpeza

**Última Atualização:** 2025-10-28
**Arquiteto de Refatoração:** Gemini Code Assist

## 1. Resumo do Estado Atual

A refatoração principal para uma arquitetura desacoplada (API Flask + SPA React) foi concluída. O projeto está na **Fase 3: Finalização e Limpeza**, com foco em robustecer a segurança, a lógica de negócio e a documentação.

As fases 0, 1 e 2 estão arquivadas e foram removidas deste plano para maior clareza.

---

## 2. Tarefas Pendentes por Prioridade

### Prioridade 1: Crítico / Alto

#### [ ] 🧠 Validar e Refinar Lógica de Análise de Scoring

- **Justificativa:** A principal funcionalidade de negócio (cálculo do `score_ponderado_final`) passou por múltiplas refatorações. É crucial garantir que o resultado final esteja 100% correto e alinhado com as regras de negócio.
- **Plano de Ação:**
  - [x] **Revisão de Código:** Analisar detalhadamente os scripts `analisar_alertas.py` e `analise_tendencia.py` em busca de "code smells", inconsistências ou bugs na lógica de cálculo.
  - [x] **Melhorar Docstrings:** Garantir que todas as funções críticas em `analisar_alertas.py` tenham docstrings claras.
  - [x] **Validação de Integração E2E (Geral):** Realizar um teste de ponta a ponta com um arquivo CSV complexo para validar a integração do sistema.
  - [x] **Validação de Regressão (Cenários Específicos):** Executar testes E2E com múltiplos arquivos CSV, cada um focado em uma regra de negócio específica. - **CONCLUÍDO**
    - [x] Cenário: Instabilidade Crônica
    - [x] Cenário: Sucesso Parcial (Closed Skipped, Canceled) - **Concluído**
    - [x] Cenário: Falha Persistente - **Concluído**
    - [x] Cenário: Sucesso Estabilizado - **Concluído**
  - [ ] **Validação de Negócio (Golden File):** Validar o resultado da análise de um arquivo CSV de produção contra o resultado esperado, definido pelo especialista de negócio.

---

### Prioridade 2: Médio

#### [ ] 🚀 Finalizar Pipeline de CI/CD

- **Justificativa:** O pipeline atual (`.github/workflows/ci.yml`) já valida o backend e o frontend, mas não constrói a imagem Docker de produção final, criando um processo de deploy manual.
- **Plano de Ação:**
  - [ ] **Modificar Build do Docker:** Alterar a etapa de build para usar o `Dockerfile` multi-estágio de produção, que constrói o frontend e o backend em uma única imagem.
  - [ ] **Publicar Imagem:** Garantir que a imagem final seja publicada no Docker Hub (ou outro registry) com as tags corretas.

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
