# 📝 Plano de Refatoração: Desacoplamento Frontend/Backend

Este documento descreve o plano estratégico e o checklist para a refatoração da arquitetura do projeto, migrando de um modelo monolítico com renderização no servidor (SSR) para uma arquitetura desacoplada, composta por um backend de API pura e um frontend Single-Page Application (SPA).

## 1. Objetivo Principal

Transformar a aplicação em um sistema moderno, onde o **backend** atua exclusivamente como uma **API RESTful** (servindo JSON) e o **frontend** é uma aplicação independente e rica (SPA) que consome essa API.

## 2. Justificativa Estratégica (Por quê?)

- **Escalabilidade Independente:** Permitir que as equipes (ou papéis) de frontend e backend evoluam e escalem seus respectivos domínios sem impactar um ao outro.
- **Flexibilidade Tecnológica:** Abrir a porta para o uso de frameworks de frontend modernos (React, Vue, Svelte) para criar uma Experiência de Usuário (UX) mais rica e reativa.
- **Contrato de API Claro:** Forçar a criação de uma API bem definida e documentada, que pode ser consumida não apenas pelo nosso frontend, mas por qualquer outro cliente no futuro (mobile, outros serviços).
- **Melhora na Experiência do Desenvolvedor (DX):** Criar uma separação clara de responsabilidades, simplificando o desenvolvimento, os testes e a depuração em cada camada.

## 3. Arquitetura Alvo

- **Backend (API Pura):**
  - O Flask (`src/app.py`) será responsável apenas por endpoints de API que recebem e retornam JSON.
  - Nenhuma rota principal irá renderizar HTML com `render_template`.
  - A autenticação será gerenciada via tokens (ex: JWT), tornando a API *stateless*.
  - Os módulos de geração de relatórios (`gerador_paginas.py`, `context_builder.py`) continuarão a existir para criar os **artefatos** de relatório (arquivos `.html` e `.csv` estáticos), que serão servidos pela API.

- **Frontend (SPA):**
  - Será um projeto separado, localizado em um novo diretório `frontend/`.
  - Construído com um framework moderno (a ser definido, ex: Vite + React).
  - Fará chamadas HTTP para a API do backend para buscar dados e acionar processos.
  - Gerenciará seu próprio estado e roteamento no lado do cliente.

- **Comunicação:**
  - A comunicação entre frontend e backend ocorrerá exclusivamente via chamadas de API RESTful.

## 6. Qualidade de Código e Segurança

A manutenção dos padrões de qualidade e segurança é um requisito não-funcional crítico desta refatoração.

- **Backend:**
  - Todo o novo código Python deve aderir aos padrões definidos no `CONTRIBUTING.md`.
  - O pipeline de CI continuará a validar formatação (`ruff format`), linting (`ruff check`) e segurança (`bandit`) para a camada de API.

- **Frontend:**
  - O novo projeto frontend (`frontend/`) deverá ser configurado com ferramentas de qualidade equivalentes.
  - **Linting:** ESLint será configurado para garantir a consistência e evitar erros comuns em TypeScript/React.
  - **Formatação:** Prettier será usado para manter um padrão de formatação de código consistente.
  - **Segurança:** O pipeline de CI incluirá um passo para verificar vulnerabilidades nas dependências do frontend (ex: `npm audit`).
  - Todas essas verificações serão adicionadas como etapas obrigatórias no workflow de CI.

## 5. Estratégia de Testes

A refatoração exige uma nova abordagem de testes. A estratégia será dividida para cobrir as responsabilidades de cada camada de forma independente e integrada.

- **Backend (API Pura):**
  - **Testes de Unidade:** Foco total na camada de serviço (`services.py`). Cada função de negócio (ex: `get_dashboard_summary`, `process_new_upload`) terá testes unitários que validam sua lógica em isolamento, sem depender do Flask ou de uma requisição HTTP.
  - **Testes de Integração:** Foco na camada de controller (`app.py`). Usaremos o cliente de teste do Flask para fazer requisições HTTP aos novos endpoints da API (`/api/v1/...`) e validar os contratos JSON (estrutura e tipos de dados) e os códigos de status HTTP. A camada de serviço será mockada para isolar a camada de API.

- **Frontend (SPA):**
  - **Testes de Unidade:** Testar componentes React individuais em isolamento usando ferramentas como `Jest` e `React Testing Library`. O objetivo é validar que, dadas certas props, o componente renderiza corretamente.
  - **Testes de Integração de Componentes:** Testar como múltiplos componentes interagem entre si. Por exemplo, validar se o preenchimento de um formulário e o clique em um botão atualizam o estado da página corretamente.

- **Testes End-to-End (E2E):**
  - Utilizaremos uma ferramenta como `Cypress` ou `Playwright` para simular fluxos de usuário completos no navegador.
  - **Exemplo de fluxo E2E:**
    1. Acessar a página de login.
    2. Fazer login como administrador.
    3. Navegar para a página de histórico.
    4. Clicar no botão de excluir de um relatório e confirmar a exclusão.
    5. Validar que o relatório desapareceu da lista.

## 4. Plano de Execução e Checklist

O trabalho será dividido em fases para mitigar riscos e permitir entregas incrementais.

### Fase 0: Preparação e Alinhamento

- [x] Criar este documento de plano (`REFACTOR_PLAN.md`).
- [x] Criar um branch de longa duração para a refatoração: `refactor/api-spa-decoupling`.
- [ ] Configurar o ambiente de desenvolvimento local para rodar os dois servidores (Flask e o dev server do frontend) simultaneamente, utilizando um proxy para evitar problemas de CORS.

---

### Fase 1: Transformar o Backend em uma API Pura

## Status: Concluída

- [x] **Implementar CORS:** Configurar o Flask para aceitar requisições do domínio do frontend em desenvolvimento.
- [x] **Refatorar Rota `GET /`:**
  - Mover a lógica de consulta ao banco de dados e cálculo de KPIs de `app.py` para uma nova função em `services.py`.
  - Transformar em `GET /api/v1/dashboard-summary`.
  - A rota deve retornar um JSON contendo os dados que hoje são passados para `index.html` (`kpi_summary`, `trend_history`, `last_action_plan`).
- [x] **Refatorar Rota `GET /relatorios`:**
  - Mover a lógica de consulta ao banco de dados de `app.py` para uma nova função em `services.py`.
  - Transformar em `GET /api/v1/reports`.
  - A rota deve retornar um JSON com a lista de metadados de todos os relatórios.
- [x] **Refatorar Rota `POST /upload`:**
  - Modificar para sempre retornar uma resposta JSON (sucesso com a URL do relatório ou erro), eliminando o `redirect`.
- [x] **Refatorar Rota de Exclusão `POST /report/delete/:id`:**
  - Garantir que a rota retorne uma resposta JSON clara de sucesso ou falha.
- [x] **Refatorar Rota `POST /compare`:**
  - Transformar em `POST /api/v1/compare` e garantir que retorne apenas JSON.
- [x] **Refatorar Autenticação:**
  - Modificar as rotas `/admin/login` e `/admin/logout` para serem stateless.
  - O login deve retornar um token (JWT) em vez de definir uma `session`.
  - As rotas protegidas (como `delete_report`) deverão validar este token enviado no cabeçalho `Authorization`.
- [x] **Limpeza:** Remover as chamadas `render_template` e outras funções/rotas obsoletas em `app.py`.
- [x] **Atualizar Testes:** Adaptar os testes existentes e criar novos testes de unidade e integração para a nova API, conforme a estratégia de testes.
  - [x] Criar teste de integração para `GET /api/v1/dashboard-summary`.
  - [x] Criar teste de integração para `GET /api/v1/reports`.
  - [x] Criar teste de integração para `POST /api/v1/upload`.
  - [x] Criar teste de integração para `DELETE /api/v1/reports/<id>` (com e sem token).
  - [x] Criar teste de integração para `POST /api/v1/compare`.

---

### Fase 2: Construir o Frontend (SPA)

O objetivo é criar a nova interface que consumirá a API desenvolvida na Fase 1.

- [x] **Estrutura do Projeto:**
  - Adicionados arquivos de configuração (`package.json`, `vite.config.ts`) para criar um projeto Vite + React + TS não-interativo.
- [x] **Configurar Qualidade de Código:** Adicionados e configurados ESLint e Prettier.
- [x] **Implementar Testes:** Configurado ambiente de testes com Vitest e React Testing Library.
- [x] **Desenvolver Componentes da UI:**
  - [x] **Página Principal (Dashboard):** Criado componente que chama `GET /api/v1/dashboard-summary` e renderiza os KPIs.
  - [x] **Componente de Upload (Análise Padrão):** Conectado o formulário de upload padrão que chama `POST /api/v1/upload`.
  - [x] **Página de Histórico:** Criada tabela de relatórios que busca dados de `GET /api/v1/reports` e permite a exclusão (com autenticação).
  - [x] **Página de Login e Autenticação:** Implementado fluxo de login completo com JWT, gerenciamento de estado de autenticação e rotas protegidas.
  - [x] **Componente de Upload (Análise Comparativa):** Conectar o formulário de upload comparativo ao endpoint `POST /api/v1/compare`.

---

### Fase 3: Finalização e Limpeza

- [ ] **Atualizar `Dockerfile`:**
  - [ ] **Corrigir Link de Retorno nos Relatórios:** Investigar e corrigir por que a `FRONTEND_BASE_URL` não está sendo aplicada corretamente nos links "Página Inicial" dos relatórios HTML gerados, que atualmente apontam para a raiz do backend em vez da home do frontend.
  - Criar um `Dockerfile` multi-estágio.
  - O primeiro estágio faz o *build* do frontend (gera os arquivos estáticos).
  - O segundo estágio copia os arquivos estáticos do frontend e a aplicação Flask.
  - Configurar um servidor web (como o Gunicorn para o Flask e talvez o Nginx para servir os estáticos) para o ambiente de produção.
- [ ] **Atualizar Pipeline de CI/CD (`.github/workflows/ci.yml`):**
  - Adicionar etapas para instalar dependências, rodar testes e fazer o build do projeto frontend.
  - Adicionar etapas para as verificações de linting, formatação e segurança do frontend.
  - Modificar a etapa de build do Docker para usar o novo `Dockerfile`.
- [ ] **Remover Código Morto:**
  - Remover os testes antigos que se tornaram obsoletos.
  - Remover o diretório `templates/` do backend (exceto os templates usados para gerar os artefatos de relatório, se houver).
  - Remover dependências do Flask que não são mais necessárias (ex: `Jinja2` se não for mais usado).
- [ ] **Atualizar Documentação:**
  - Atualizar o `GEMINI.md` e `README.md` para refletir a nova arquitetura de API + SPA.
  - **Revisar e reescrever a documentação técnica (`docs/doc_tecnica.html`)** para alinhar com a nova arquitetura.
  - Marcar este plano (`REFACTOR_PLAN.md`) como concluído.
