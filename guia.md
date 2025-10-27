# 🗺️ Guia de Navegação do Projeto `meu-dash`

Este documento serve como um mapa central para a documentação do projeto `meu-dash`. Ele foi criado para ajudar você a navegar pelos diversos arquivos `.md` e entender onde encontrar as informações relevantes para cada fase ou aspecto do projeto.

Nosso objetivo é transformar a complexidade em clareza, permitindo que você atue de forma mais granular e eficiente.

---

## 🚀 Visão Geral do Projeto

O `meu-dash` é uma aplicação web que automatiza a análise de alertas de monitoramento, agrupando-os em "Casos" e calculando um "Score de Prioridade Ponderado". Ele é composto por um backend em Python (Flask) e um frontend em React (SPA), comunicando-se via API RESTful.

Para uma introdução rápida e o propósito de negócio, consulte:

* **README.md**: A porta de entrada principal do projeto.

---

## 🧭 Fases e Domínios de Interesse

Abaixo, você encontrará os principais domínios de informação do projeto, com links diretos para os documentos que os detalham.

### 1. Visão Geral e Propósito de Negócio

* **Onde encontrar:** **README.md**
* **O que você encontrará:**
  * Resumo do projeto e seu valor.
  * Como iniciar o ambiente de desenvolvimento local.
  * Tecnologias utilizadas.
  * Lógica de análise de negócio.
  * Links para a documentação da API (Swagger).

### 2. Arquitetura e Design do Sistema

* **Onde encontrar:** **ARCHITECTURE.md** e **docs/adrs/**
* **O que você encontrará:**
  * Visão geral da arquitetura desacoplada (API + SPA).
  * Diagramas de componentes e fluxo de dados.
  * Detalhes sobre os componentes principais do backend e frontend.
  * **ADRs (Architecture Decision Records)**: Registros das decisões arquitetônicas importantes e seus "porquês".

### 3. Contribuição e Desenvolvimento

* **Onde encontrar:** **CONTRIBUTING.md**
* **O que você encontrará:**
  * Guia detalhado para configurar o ambiente de desenvolvimento.
  * Padrões de código e qualidade (formatação, linting, segurança).
  * Como executar os testes (unitários, integração, E2E).
  * Processo de Pull Request.

### 4. Plano de Refatoração e Débito Técnico

* **Onde encontrar:** **REFACTOR_PLAN.md**
* **O que você encontrará:**
  * O plano de ação atual para refatorações e resolução de débito técnico.
  * Tarefas pendentes, priorizadas por impacto e risco.
  * Justificativas e planos de ação detalhados para cada item.

### 5. Histórico de Ações e Decisões

* **Onde encontrar:** **DIARIO_DE_BORDO.md**
* **O que você encontrará:**
  * Um registro cronológico de todas as ações significativas, diagnósticos e decisões tomadas ao longo do projeto.
  * É a memória de longo prazo do projeto.

---

## 💡 Como Usar Este Guia

1. **Comece por aqui:** Se você está perdido ou procurando por algo específico, este `guia.md` é seu ponto de partida.
2. **Identifique a fase/domínio:** Encontre a seção que corresponde ao seu interesse atual (ex: "Quero entender a arquitetura" -> vá para a seção 2).
3. **Navegue para o documento específico:** Use os links fornecidos para ir diretamente ao documento detalhado.

Este guia será mantido atualizado para refletir a estrutura da documentação do projeto.
