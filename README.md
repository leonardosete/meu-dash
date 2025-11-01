# 🕵️‍♂️📈 Aplicação Web para Análise de Alertas e Tendências

[![CI - Build, Test, and Publish](https://github.com/leonardosete/meu-dash/actions/workflows/ci.yml/badge.svg)](https://github.com/leonardosete/meu-dash/actions/workflows/ci.yml)

Esta é uma aplicação web que automatiza a análise de alertas de monitoramento, permitindo que equipes foquem em problemas críticos através de um **Score de Prioridade Ponderado**.

---

## 🧭 Navegação

- **[Guia de Arquitetura (`ARCHITECTURE.md`)](./ARCHITECTURE.md)**: Entenda a estrutura do sistema e o fluxo de dados.
- **[Como Contribuir (`CONTRIBUTING.md`)](./CONTRIBUTING.md)**: Padrões e processos para desenvolver.
- **[Documentação Gerencial](https://leonardosete.github.io/meu-dash/doc_gerencial.html)**: Visão geral do projeto para stakeholders.
- **[Documentação Técnica](https://leonardosete.github.io/meu-dash/doc_tecnica.html)**: Detalhes técnicos e de implementação.

---

### 🚀 Fluxo de Desenvolvimento (CI/CD-First)

Este projeto adota uma filosofia **CI/CD-First**, o que significa que o desenvolvimento, teste e build são centralizados no pipeline de CI/CD do GitHub Actions. Não há mais um ambiente de desenvolvimento local completo com `docker-compose`.

O fluxo de trabalho para contribuir é:

1. **Codificar Localmente:** Faça suas alterações no código-fonte.
2. **Validar Localmente (Opcional):** Use os comandos do `Makefile.mk` (ex: `make check`, `make test`) para validar suas alterações antes do commit.
3. **Versionar:** Faça o commit e o push para uma nova branch.
4. **Validação Automática:** O GitHub Actions executará todos os testes e verificações de qualidade.
5. **Build da Imagem:** Se a validação for bem-sucedida, uma nova imagem Docker será construída e publicada no registry.
6. **Deploy Manual:** A nova imagem pode ser implantada no ambiente Kubernetes manualmente.

Para mais detalhes sobre como contribuir, padrões de código e o processo de Pull Request, consulte o **Guia de Contribuição (`CONTRIBUTING.md`)**.

---

### 💻 Tecnologias Utilizadas

- **Backend:**
  - **Framework:** Python / Flask
  - **Análise de Dados:** Pandas / NumPy
  - **Banco de Dados:** SQLite / SQLAlchemy
  - **Qualidade e Testes:** Pytest / Ruff / Bandit
- **Frontend:**
  - **Framework:** React (com Vite)
  - **Linguagem:** TypeScript
  - **Qualidade e Testes:** ESLint / Prettier / Vitest
- **Infraestrutura:**
  - **Containerização:** Docker / Docker Compose
  - **Containerização:** Docker

---

## 🚀 Como Usar

Acesse a aplicação através do seu endereço web e faça o upload de um ou mais arquivos `.csv` contendo os dados de alerta. A aplicação processará os arquivos e gerará os relatórios automaticamente.

---

### 💡 Lógica de Análise

O sistema utiliza uma abordagem inteligente para transformar "ruído" (milhares de alertas) em insights acionáveis.

#### 🆚 Casos vs. Alertas

Para focar na causa raiz, a análise distingue **Alertas** de **Casos**:

- **Alerta:** Uma notificação individual de um evento de monitoramento.
- **Caso:** A causa raiz de um problema. Ele agrupa múltiplos alertas do mesmo tipo que ocorrem em um mesmo recurso (CI/Nó).

> **Exemplo:** Um servidor com 100 alertas de "disco cheio" é tratado como **1 Caso**, permitindo focar na solução do problema raiz.

#### ⚖️ Score de Prioridade Ponderado

A criticidade de um caso é calculada através de um **Score de Prioridade Ponderado**, que considera fatores como Risco, Ineficiência da automação e Impacto (volume de alertas).

A justificativa e os detalhes desta decisão arquitetônica estão documentados em **[ADR 001: Definição do Score de Prioridade Ponderado](./docs/adrs/001-definicao-do-score-de-prioridade.md)**.

---

### 📁 Estrutura do Projeto

A arquitetura é desacoplada em duas partes principais:

- `backend/`: Contém a aplicação Flask que serve a API RESTful.
  - `src/`: O código-fonte da API.
  - `tests/`: Os testes para a API.
- `frontend/`: Contém a Single-Page Application (SPA) em React.
  - `src/`: O código-fonte e os componentes da UI.
- `data/`: Diretório persistido para armazenar uploads e relatórios gerados.
- `docs/`: Documentação geral do projeto (arquitetura, ADRs, etc.).

---

### 📖 Documentação

A documentação técnica e gerencial do projeto está disponível publicamente e pode ser acessada online através dos links abaixo:

- **Documentação Gerencial:** [https://leonardosete.github.io/meu-dash/doc_gerencial.html](https://leonardosete.github.io/meu-dash/doc_gerencial.html)
- **Documentação Técnica:** [https://leonardosete.github.io/meu-dash/doc_tecnica.html](https://leonardosete.github.io/meu-dash/doc_tecnica.html)

---

### 📄 Formato do Arquivo de Entrada (Schema CSV)

Para que a análise seja executada corretamente, o arquivo `.csv` enviado deve conter as seguintes colunas obrigatórias. A ordem não importa, mas os nomes devem ser exatos.

<details>
<summary><strong>Clique para expandir e ver a lista de colunas obrigatórias</strong></summary>

```
- sys_created_on
- number
- short_description
- severity
- node
- cmdb_ci
- assignment_group
- source
- sn_priority_group
- state
- sys_id
- u_closed_date
- metric_name
- message_key
- Pilar
- tasks_count
- tasks_numbers
- tasks_status
- has_remediation_task
- alert_found
```

</details>

---

### ✨ Principais Funcionalidades

1. 🧠 **Análise Inteligente**: Identifica problemas únicos (Casos) e os prioriza com base em Risco, Ineficiência e Impacto.
2. 📊 **Geração de Relatórios**: Cria dashboards HTML interativos com KPIs, gráficos e uma seção de "Conceitos" que explica a lógica da análise.
3. 📋 **Planos de Ação Acionáveis**: O "Diagnóstico Rápido" no relatório de tendência oferece um link direto para um plano de ação pré-filtrado por squad (`atuar-<squad>.html`), conectando o insight à ação e facilitando a delegação.
4. 📈 **Análise Comparativa**: A cada novo upload, o sistema identifica o último período analisado e gera um relatório comparativo (`comparativo_periodos.html`), criando uma cadeia contínua de comparações que mostra a evolução dos problemas, a taxa de resolução e os problemas persistentes ao longo do tempo.
5. ✅ **Validação da Qualidade dos Dados**: Detecta e isola alertas com dados de remediação inválidos (`qualidade_dados_remediacao.html`=> `invalid_has_remediation_task.csv`), garantindo a confiabilidade da análise e notificando no dashboard principal.
6. 🗂️ **Histórico de Análises**: Mantém um histórico de todas as análises geradas, permitindo acesso rápido aos relatórios padrão e comparativos anteriores.
7. 🗑️ **Gerenciamento de Relatórios**: Permite a exclusão de relatórios individuais diretamente pela interface de histórico, liberando espaço e mantendo o ambiente organizado.
8. 🧠 **Navegação Contextual Inteligente**: O dashboard de KPIs centraliza os links de ação para o Relatório Completo, Plano de Ação e Análise Comparativa, permitindo que o usuário navegue diretamente do insight para a ação com um único clique.

---

### 🐳 Implantação no Kubernetes

A aplicação está totalmente containerizada e pronta para ser implantada em um ambiente Kubernetes. Os manifestos de implantação foram consolidados no arquivo `kubernetes.yaml`.

Para implantar a aplicação, execute:

```bash
kubectl apply -f kubernetes.yaml
```

Isso irá criar um `Deployment` com 2 réplicas da aplicação e um `Service` do tipo `LoadBalancer` para expor a aplicação.
