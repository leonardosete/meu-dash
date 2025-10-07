# 🤖 PAINEL DE CONTROLE DA IA (GEMINI)

## 1. SEU PAPEL E OBJETIVO

**Você é um engenheiro de software sênior especialista em arquitetura de sistemas**, atuando como o principal assistente para o projeto `meu-dash`.

**Seu objetivo principal é auxiliar no desenvolvimento, análise, depuração e documentação deste projeto**, garantindo que o código e a documentação permaneçam consistentes e de alta qualidade.

## 2. CONTEXTO E FONTE DA VERDADE

- **Diretório Raiz do Projeto:** `~/meu-dash`
- **Fonte Primária da Verdade:** **Este arquivo (`GEMINI.md`) é sua referência principal.** Sempre comece lendo-o para entender a arquitetura e o fluxo de dados. O código-fonte em `src/app.py` é a autoridade final sobre o fluxo de execução.
- **Documentação para Humanos:**
  - `docs/doc_tecnica.html`: Detalhes técnicos da implementação.
  - `docs/doc_gerencial.html`: Visão de alto nível e impacto para gestão.

## 3. REGRAS DE OPERAÇÃO

1. **Sincronização Obrigatória:** Qualquer alteração no código que afete o fluxo de execução, as entradas/saídas de um módulo ou a estrutura dos relatórios gerados **DEVE** ser refletida imediatamente neste arquivo.
2. **Análise Baseada em Fatos:** Suas análises devem se basear estritamente na arquitetura e no fluxo descritos aqui. Não presuma funcionalidades que não estejam documentadas.
3. **Clareza e Precisão:** Ao gerar código ou documentação, seja explícito sobre as dependências entre os módulos e os artefatos que eles consomem e produzem.
4. **Ponto de Partida Fixo:** Toda análise de fluxo de execução começa pela interação do usuário com a interface web, orquestrada pelo `src/app.py`.

---

## 📝 DESCRIÇÃO DO PROJETO: Análise de Alertas e Tendências

Este projeto é uma **aplicação web Flask** que automatiza a análise de alertas de monitoramento (`.csv`), gera um ecossistema de dashboards HTML interativos e identifica tendências de problemas ao longo do tempo. A aplicação é projetada para ser executada em contêiner (Docker) e implantada em Kubernetes.

O sistema classifica os problemas com base em um **Score de Prioridade Ponderado**, que considera o risco do negócio, a ineficiência da automação e o impacto operacional (volume de alertas).

---

## 🧠 LÓGICA DE ANÁLISE E PRIORIZAÇÃO

A análise se baseia em conceitos-chave para transformar "ruído" (alertas) em insights acionáveis (casos priorizados).

### Casos vs. Alertas

- **Alerta:** Uma notificação individual de um evento de monitoramento.
- **Caso:** A causa raiz de um problema. Agrupa múltiplos alertas do mesmo tipo em um mesmo recurso (CI/Nó).

### Score de Prioridade Ponderado

### **Score Final = (Risco) * (Ineficiência) * (Impacto)**

- **Risco:** Gravidade inerente do problema (baseado na severidade e prioridade).
- **Ineficiência:** Penaliza falhas da automação de remediação.
- **Impacto:** Penaliza o "ruído" operacional (volume de alertas).

---

## 🏛️ ARQUITETURA E COMPONENTES

A arquitetura do projeto é centrada em uma aplicação web Flask que orquestra todo o processo de análise e visualização.

### 1. Orquestrador Principal: Aplicação Flask (`src/app.py`)

- **Responsabilidade:** Ponto de entrada da aplicação web. Gerencia as rotas (endpoints), as requisições do usuário e delega a lógica de negócio para a camada de serviço. Atua como um "controlador" enxuto.
- **Componentes Internos:**
  - **Flask:** Microframework web.
  - **SQLAlchemy:** ORM para interagir com o banco de dados.
  - **Flask-Migrate:** Gerencia as migrações do esquema do banco de dados.
- **Rotas Principais:**
  - `GET /`: Exibe a página inicial de upload (`upload.html`).
  - `POST /upload`: Recebe o arquivo do usuário e chama o `services.py` para processá-lo.
  - `POST /compare`: Recebe dois arquivos e chama o serviço de comparação direta.
  - `GET /relatorios`: Exibe um histórico de todos os relatórios gerados, com links para visualizá-los.
  - `GET /reports/<run_folder>/<filename>`: Serve os arquivos de relatório (HTML, CSV, etc.) de uma execução específica.

### 2. Camada de Serviço (`src/services.py`)

- **Responsabilidade:** Contém a lógica de negócio principal da aplicação. Orquestra todo o fluxo de trabalho para a geração de um relatório, desde o recebimento do arquivo até a gravação no banco de dados.
- **Invocação:** É chamado pelo `app.py` (controlador) quando uma nova análise é solicitada.
- **Fluxo Interno:**
  1. Salva o arquivo de upload.
  2. Consulta o banco de dados pelo relatório anterior.
  3. Orquestra a análise de tendência (chamando `analisar_alertas` e `analise_tendencia`).
  4. Orquestra a análise principal completa (chamando `analisar_alertas`).
  5. Constrói o dicionário de contexto (chamando `context_builder`).
  6. Orquestra a geração de todas as páginas HTML (chamando `gerador_paginas`).
  7. Salva o novo registro do relatório no banco de dados.
- **Funções Adicionais:** Contém também a lógica para a `process_direct_comparison`, que analisa dois arquivos e gera um relatório de tendência.

### 2. Banco de Dados (`data/meu_dash.db`)

- **Tecnologia:** SQLite, gerenciado pelo SQLAlchemy.
- **Modelo (`Report`):**
  - `id`: Identificador único.
  - `timestamp`: Data e hora da análise.
  - `original_filename`: Nome do arquivo `.csv` que foi enviado.
  - `report_path`: Caminho para o relatório HTML principal (`resumo_geral.html`).
  - `json_summary_path`: **Crucial para a análise de tendência.** Caminho para o arquivo `resumo_problemas.json` daquela análise.
  - `date_range`: (Opcional) String que armazena o intervalo de datas coberto pelo relatório (ex: "01/01/2023 a 15/01/2023").
- **Responsabilidade:** Manter um histórico de todas as análises executadas. Isso permite que a análise de tendência compare o upload **atual** com a análise **mais recente** registrada no banco, criando um sistema com estado.

### 3. Motores de Análise (Invocados como Bibliotecas)

#### Módulo: `src/analisar_alertas.py`

- **Responsabilidade:** Atua como um motor de análise de dados puro. Sua única função é processar um arquivo de alertas (`.csv`) e gerar os artefatos de **dados** (outros `.csv` e um `resumo_problemas.json`). **Não possui conhecimento sobre HTML ou apresentação.**
- **Invocação:** É chamado pela camada de serviço (`services.py`).
- **Saídas (Outputs):** Retorna um dicionário contendo os DataFrames da análise e os caminhos para os arquivos de dados gerados.

#### Módulo: `src/analise_tendencia.py`

- **Responsabilidade:** Comparar dois períodos (JSON atual vs. JSON anterior) e gerar o `resumo_tendencia.html`.
- **Invocação:** É chamado pela camada de serviço (`services.py`) durante o fluxo de comparação. Também pode ser executado como um script de linha de comando independente para testes.
- **Entradas (Inputs):** Recebe os caminhos para os dois arquivos JSON (`json_anterior`, `json_atual`), os nomes dos arquivos CSV originais, o caminho de saída para o relatório HTML e, opcionalmente, os intervalos de datas de ambos os períodos e um booleano (`is_direct_comparison`) que ajusta a navegação no relatório final.

### 4. Camada de Apresentação

#### Módulo: `src/context_builder.py`

- **Responsabilidade:** Preparar os dados para a visualização. Recebe os resultados brutos da análise (DataFrames) e os transforma em um dicionário de `contexto` com todas as métricas, KPIs e listas de "Top 5" necessárias para renderizar os dashboards.

#### Módulos: `src/gerador_paginas.py` e `src/gerador_html.py`

- **Responsabilidade:** Renderizar os relatórios HTML. Recebem o `contexto` e os dados necessários e geram os arquivos `.html` finais. São componentes de apresentação puros, sem lógica de negócio.

### 4. Templates e Dados

- **`templates/`:** Contém todos os templates HTML usados pelo Flask para renderizar as páginas da aplicação (`upload.html`, `relatorios.html`, etc.).
- **`data/`:** Diretório persistido que armazena:
  - `uploads/`: Cópias dos arquivos `.csv` originais enviados pelo usuário.
  - `reports/`: Subdiretórios para cada execução (`run_...`), contendo todos os artefatos gerados (HTML, JSON, CSV).
  - `meu_dash.db`: O arquivo do banco de dados SQLite.

---

## 🌊 FLUXO DE EXECUÇÃO LÓGICO

O processo é iniciado pela interação do usuário e orquestrado integralmente pelo `app.py`.

1. **Usuário:** Acessa a rota `/` e vê a página de upload.
2. **Upload:** O usuário seleciona um arquivo `.csv` (`file_atual`) e o envia através do formulário (`POST /upload`).
3. **Controlador (`app.py`):** A rota `/upload` recebe a requisição e imediatamente chama a camada de serviço, passando o arquivo.
4. **Serviço (`services.py`):** A função `process_upload_and_generate_reports` assume o controle e executa a lógica de negócio:
    a. **Salva o arquivo** e cria um diretório de saída para a execução (`run_<timestamp>`).
    b. **Consulta o DB** para obter o relatório mais recente.
    c. **Executa a Análise de Tendência (se aplicável):**
        i. Chama `analisar_alertas.py` em modo `light_analysis=True` para gerar o JSON do período atual.
        ii. Chama `analise_tendencia.py` para comparar os JSONs (atual vs. anterior) e gerar o `resumo_tendencia.html`.
    d. **Executa a Análise Principal:** Chama `analisar_alertas.py` em modo `light_analysis=False` para obter os DataFrames da análise completa e gerar os CSVs de dados.
    e. **Constrói o Contexto:** Chama `context_builder.py`, passando os DataFrames, para obter um dicionário de `contexto` com todos os KPIs e dados para os gráficos.
    f. **Gera as Páginas:** Chama as funções em `gerador_paginas.py`, passando o `contexto`, para renderizar todos os relatórios HTML.
    g. **Persiste o Resultado:** Cria um novo registro `Report` no banco de dados com os caminhos para os artefatos gerados.
5. **Redirecionamento (`app.py`):** O serviço retorna as informações necessárias para o `app.py`, que então redireciona o navegador do usuário para o `resumo_geral.html` recém-criado.

### Fluxo de Comparação Direta

1. **Usuário:** Acessa a seção "Análise Comparativa Direta", seleciona dois arquivos `.csv` e clica em "Comparar".
2. **Controlador (`app.py`):** A rota `POST /compare` recebe os dois arquivos e chama a função `services.process_direct_comparison`.
3. **Serviço (`services.py`):** A função `process_direct_comparison` orquestra o fluxo:
    a. Salva os dois arquivos temporariamente e os ordena por data.
    b. Chama `analisar_alertas.py` para cada arquivo, gerando os respectivos `resumo_problemas.json`.
    c. Chama `gerar_contexto_tendencia` para obter os dados da comparação.
5. **Controlador (`app.py`):** O serviço retorna o `contexto` e os `metadados`. O controlador então usa `render_template` para gerar o HTML e redireciona o usuário para a visualização.

---

## 📦 ARTEFATOS GERADOS (OUTPUTS)

Todos os artefatos são gerados dentro de um subdiretório `run_<timestamp>` em `data/reports/` e servidos dinamicamente pela aplicação Flask.

### Dashboards HTML Interativos

- **`resumo_geral.html`**: Visão geral gerencial do período atual. Ponto central de navegação.
- **`resumo_tendencia.html`**: (Condicional) Relatório de evolução entre o período atual e o anterior.
- **`editor_atuacao.html`**: Editor interativo para o time atuar sobre os problemas.
- ... (e todos os outros relatórios)

### Arquivos de Dados

- **`resumo_problemas.json`**: A base de dados da análise, usada para gerar relatórios e para a próxima análise de tendência.
- **`atuar.csv`**: Lista de problemas que exigem ação manual.
- ... (e todos os outros arquivos de dados)
