# ✅ Plano de Ação: Finalização e Limpeza (Pós-Refatoração)

**Data do Diagnóstico:** 2024-10-27
**Arquiteto de Refatoração:** Gemini Code Assist

## 1. Resumo do Estado Atual

A refatoração principal de desacoplamento (API + SPA) foi concluída com sucesso. O projeto está agora na **Fase 3: Finalização e Limpeza**. Este documento detalha as tarefas pendentes, priorizadas por impacto e risco, para levar o projeto a um estado de prontidão para produção.

As fases 0, 1 e 2 estão arquivadas e foram removidas deste plano para maior clareza.

---

## 2. Tarefas Pendentes por Prioridade

### Prioridade 1: Crítico

#### [x] 🛡️ Revisão e Reforço da Autenticação

- **Justificativa:** O fluxo de autenticação JWT está funcional, mas requer uma validação de segurança e usabilidade completa antes da produção. Uma falha aqui representa um risco de segurança direto.
- **Plano de Ação:**
  - [x] **Validação E2E:** Realizar testes de ponta a ponta para o fluxo de login, logout e acesso a rotas protegidas (ex: exclusão de relatório) em um ambiente de produção simulado.
  - [x] **Consistência da UI:** Garantir que a interface reaja de forma consistente ao estado de autenticação (ex: exibir/ocultar o card "Modo Admin" e o botão de exclusão).
  - [x] **Revisão de Segurança:** Analisada e corrigida a implementação do JWT (expiração do token e `SECRET_KEY` agora são configuráveis via variáveis de ambiente).

---

### Prioridade 2: Alto

#### [x] 🧠 Refinar Lógica de Análise com Novas Colunas

- **Justificativa:** A principal funcionalidade de negócio (cálculo do score de prioridade) não está utilizando a lógica mais recente, que depende de novas colunas no CSV de entrada. Isso significa que o valor gerado pela ferramenta está incompleto.
- **Contexto (Nova Estrutura de Colunas):**

  ```
  Duração;sys_created_on;assignment_group;short_description;node;cmdb_ci;number;severity;parent;cmdb_ci.sys_class_name;source;sn_priority_group;state;sys_id;type.display_value;u_action_time;u_closed_date;acknowledged;correlation_group;event_count;incident;metric_name;message_key;com_remediacao;Pilar;tasks_count;tasks_numbers;tasks_status;remediation_tasks_present;alert_found;processing_status;error_message
  ```

- **Plano de Ação:**
  - [x] **Atualizar Constantes:** Adicionar as novas colunas ao `backend/src/constants.py` e atualizar a lista `ESSENTIAL_COLS`.
  - [x] **Adaptar Ingestão:** Modificar a função `carregar_dados` em `analisar_alertas.py` para processar o novo formato.
  - [x] **Implementar Lógica:** Incorporar a coluna `tasks_status` no cálculo do "Score de Ineficiência" e no `score_ponderado_final`.
  - [x] **Atualizar e Robustecer Testes Unitários:** Garantir que a nova lógica de scoring, incluindo o `fator_ineficiencia_task`, esteja completamente coberta por testes.
  - [ ] **Validação Funcional E2E (Mundo Real):** Realizar teste de ponta a ponta com um arquivo CSV real, extraído do ambiente de produção, para validar a robustez do "porteiro" de dados (`carregar_dados`) e a precisão do cálculo do "Score Ponderado Final".
  - [x] **Validação Funcional E2E:** Realizar teste de ponta a ponta com um arquivo real para validar o cálculo do "Score Ponderado Final" e garantir que a documentação da funcionalidade está visível no relatório.

#### [ ] � Aprofundar Análise de Eficácia da Remediação

- **Justificativa:** A análise atual confirma a *execução* da automação (baseado na existência e status da task), mas não a sua *eficácia* real em resolver a causa raiz. O relatório `resumo_geral.html` destaca essa limitação como um "Ponto de Atenção".
- **Plano de Ação:**
  - [ ] **Workshop com Time de Automação:** Realizar uma sessão para mapear o significado detalhado dos status de fechamento das tarefas de remediação (REM00XXXXX).
  - [ ] **Extrair Novos Dados:** Identificar se é possível extrair informações mais granulares sobre o sucesso da remediação a partir dos sistemas de origem.
  - [ ] **Refinar Score de Ineficiência:** Atualizar a lógica de cálculo do score para incorporar os novos insights, tornando a priorização ainda mais precisa e alinhada com a realidade operacional.

#### [ ] �🚀 Atualizar Pipeline de CI/CD

- **Justificativa:** O pipeline atual (`.github/workflows/ci.yml`) não valida o código do frontend nem constrói a imagem Docker de produção final, criando um ponto cego de qualidade e um processo de deploy manual.
- **Plano de Ação:**
  - [ ] **Adicionar Etapas do Frontend:** Integrar no CI os comandos para instalar dependências (`npm install`), rodar lint (`npm run lint`) e testes (`npm run test`) do frontend.
  - [ ] **Modificar Build do Docker:** Alterar a etapa de build para usar o `Dockerfile` multi-estágio de produção, que constrói o frontend e o backend em uma única imagem.
  - [ ] **Publicar Imagem:** Garantir que a imagem final seja publicada no Docker Hub (ou outro registry) com as tags corretas.

---

### Prioridade 3: Médio

#### [ ] 🧹 Remover Código Morto

- **Justificativa:** A existência de código e dependências não utilizadas (como o diretório `templates/` e rotas de renderização no backend) aumenta a carga cognitiva e a complexidade acidental do projeto.
- **Plano de Ação:**
  - [ ] **Remover Diretório `templates/`:** Excluir o diretório `backend/templates/`, pois a API não renderiza mais HTML diretamente.
  - [ ] **Remover Rotas Obsoletas:** Garantir que todas as chamadas `render_template` e as rotas associadas foram removidas de `app.py`.
  - [ ] **Limpar Dependências:** Analisar o `requirements.txt` e remover pacotes que não são mais necessários (ex: `Jinja2`, se não for mais usado para gerar os artefatos de relatório).

#### [ ] 📚 Atualizar Documentação

- **Justificativa:** Documentação desatualizada ou inconsistente é um débito técnico que gera confusão e pode levar a erros.
- **Plano de Ação:**
  - [ ] **Consolidar Documentação Técnica:** Substituir a antiga `doc_tecnica.html` pela documentação da API gerada pelo Flasgger (`/apidocs`), atualizando todos os links no `README.md`.
  - [ ] **Revisar Documentação Gerencial:** Ajustar o texto da `doc_gerencial.html` para refletir o estado atual e o valor da ferramenta.
  - [ ] **Atualizar `README.md`:** Revisar o `README.md` para garantir que ele reflete a arquitetura final e os novos processos.
  - [ ] **Finalizar este Plano:** Ao concluir todas as tarefas, marcar este documento como concluído e arquivá-lo.

---

### Prioridade 4: Baixo

#### [ ] ⚙️ Consolidar Ferramentas de Qualidade

- **Justificativa:** O arquivo `pyproject.toml` contém uma configuração para a ferramenta `black`, mas o projeto padronizou o uso de `Ruff` para formatação e linting. É uma pequena inconsistência que deve ser corrigida.
- **Plano de Ação:**
  - [ ] **Remover Configuração do Black:** Excluir a seção `[tool.black]` do arquivo `pyproject.toml` para eliminar a ambiguidade.
