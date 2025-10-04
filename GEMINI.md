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

1.  **Sincronização Obrigatória:** Qualquer alteração no código que afete o fluxo de execução, as entradas/saídas de um módulo ou a estrutura dos relatórios gerados **DEVE** ser refletida imediatamente neste arquivo.
2.  **Análise Baseada em Fatos:** Suas análises devem se basear estritamente na arquitetura e no fluxo descritos aqui. Não presuma funcionalidades que não estejam documentadas.
3.  **Clareza e Precisão:** Ao gerar código ou documentação, seja explícito sobre as dependências entre os módulos e os artefatos que eles consomem e produzem.
4.  **Ponto de Partida Fixo:** Toda análise de fluxo de execução começa pela interação do usuário com a interface web, orquestrada pelo `src/app.py`.

---

# 📝 DESCRIÇÃO DO PROJETO: Análise de Alertas e Tendências

Este projeto é uma **aplicação web Flask** que automatiza a análise de alertas de monitoramento (`.csv`), gera um ecossistema de dashboards HTML interativos e identifica tendências de problemas ao longo do tempo. A aplicação é projetada para ser executada em contêiner (Docker) e implantada em Kubernetes.

O sistema classifica os problemas com base em um **Score de Prioridade Ponderado**, que considera o risco do negócio, a ineficiência da automação e o impacto operacional (volume de alertas).

---

# 🧠 LÓGICA DE ANÁLISE E PRIORIZAÇÃO

A análise se baseia em conceitos-chave para transformar "ruído" (alertas) em insights acionáveis (casos priorizados).

## Casos vs. Alertas
- **Alerta:** Uma notificação individual de um evento de monitoramento.
- **Caso:** A causa raiz de um problema. Agrupa múltiplos alertas do mesmo tipo em um mesmo recurso (CI/Nó).

## Score de Prioridade Ponderado
**Score Final = (Risco) * (Ineficiência) * (Impacto)**
- **Risco:** Gravidade inerente do problema (baseado na severidade e prioridade).
- **Ineficiência:** Penaliza falhas da automação de remediação.
- **Impacto:** Penaliza o "ruído" operacional (volume de alertas).

---

# 🏛️ ARQUITETURA E COMPONENTES

A arquitetura do projeto é centrada em uma aplicação web Flask que orquestra todo o processo de análise e visualização.

## 1. Orquestrador Principal: Aplicação Flask (`src/app.py`)

- **Responsabilidade:** Único ponto de entrada e cérebro do projeto. Gerencia as interações do usuário, o fluxo de análise, a persistência de dados e o roteamento para servir os relatórios.
- **Componentes Internos:**
    - **Flask:** Microframework web.
    - **SQLAlchemy:** ORM para interagir com o banco de dados.
    - **Flask-Migrate:** Gerencia as migrações do esquema do banco de dados.
- **Rotas Principais:**
    - `GET /`: Exibe a página inicial de upload (`upload.html`).
    - `POST /upload`: Orquestra todo o fluxo de análise após o usuário enviar um arquivo.
    - `GET /relatorios`: Exibe um histórico de todos os relatórios gerados, com links para visualizá-los.
    - `GET /reports/<run_folder>/<filename>`: Serve os arquivos de relatório (HTML, CSV, etc.) de uma execução específica.
    - `GET /health`: Endpoint de health check para Kubernetes. Retorna um JSON `{'status': 'ok'}`.
    - `GET /docs/<path:filename>`: Serve a documentação estática do projeto (e.g., `doc_tecnica.html`).

## 2. Banco de Dados (`data/meu_dash.db`)

- **Tecnologia:** SQLite, gerenciado pelo SQLAlchemy.
- **Modelo (`Report`):**
    - `id`: Identificador único.
    - `timestamp`: Data e hora da análise (quando o processo foi executado).
    - `original_filename`: Nome do arquivo `.csv` que foi enviado.
    - `report_path`: Caminho para o relatório HTML principal (`resumo_geral.html`).
    - `json_summary_path`: **Crucial para a análise de tendência.** Caminho para o arquivo `resumo_problemas.json` daquela análise.
    - `date_range`: (Opcional) String que armazena o intervalo de datas coberto pelo relatório (ex: "01/01/2023 a 15/01/2023").
    - `max_date`: (Opcional) **Novo campo fundamental.** Armazena o objeto de data correspondente à data mais recente do *conteúdo* do arquivo de input.
- **Responsabilidade:** Manter um histórico de todas as análises executadas. A comparação para análise de tendência agora é mais inteligente: em vez de apenas pegar a última análise executada, o sistema usa o campo `max_date` para encontrar a análise anterior mais relevante cujo conteúdo seja cronologicamente anterior ao do upload atual.

## 3. Motores de Análise (Invocados como Bibliotecas)

#### Módulo: `src/analisar_alertas.py`
- **Responsabilidade:** Processar um único arquivo de alertas, realizar a análise principal e orquestrar a geração dos relatórios HTML para aquele período.
- **Invocação:** É chamado como uma função Python diretamente do `app.py`.
- **Entradas (Inputs):** Recebe o caminho do arquivo de input e o diretório de output como argumentos de função. A flag `light_analysis` controla a profundidade da análise.
- **Saídas (Outputs):** Retorna um dicionário contendo os caminhos para os artefatos gerados (HTML e JSON).

#### Módulo: `src/analise_tendencia.py`
- **Responsabilidade:** Comparar dois períodos (JSON atual vs. JSON anterior) e gerar o `resumo_tendencia.html`.
- **Invocação:** É chamado como uma função Python diretamente do `app.py`.
- **Entradas (Inputs):** Recebe os caminhos para os dois arquivos JSON (`json_anterior`, `json_atual`) e os nomes dos arquivos CSV originais como argumentos de função.

## 4. Templates e Dados

- **`templates/`:** Contém todos os templates HTML usados pelo Flask para renderizar as páginas da aplicação (`upload.html`, `relatorios.html`, etc.).
- **`data/`:** Diretório persistido que armazena:
    - `uploads/`: Cópias dos arquivos `.csv` originais enviados pelo usuário.
    - `reports/`: Subdiretórios para cada execução (`run_...`), contendo todos os artefatos gerados (HTML, JSON, CSV).
    - `meu_dash.db`: O arquivo do banco de dados SQLite.

---

# 🌊 FLUXO DE EXECUÇÃO LÓGICO

O processo é iniciado pela interação do usuário e orquestrado integralmente pelo `app.py`.

1.  **Usuário:** Acessa a rota `/` e vê a página de upload.
2.  **Upload:** O usuário seleciona um arquivo `.csv` (`file_atual`) e o envia através do formulário (`POST /upload`).
3.  **Orquestração (`app.py`):
    a. **Salvar e Extrair Datas:** O arquivo `.csv` enviado é salvo em `data/uploads/`. O módulo `get_date_range.py` é usado para extrair o intervalo de datas do arquivo. Um diretório de saída (`run_<timestamp>`) é criado em `data/reports/`.
    b. **Buscar Histórico Relevante:** O `app.py` consulta o banco de dados para encontrar o relatório anterior mais apropriado para comparação, buscando pelo campo `max_date` (`Report.query.order_by(Report.max_date.desc()).first()`).
    c. **Condição: Análise de Tendência (se um relatório anterior existe):**
        i. **Análise Leve:** A função `analisar_arquivo_csv` é chamada com `light_analysis=True` para o arquivo **atual**, gerando rapidamente o `resumo_problemas.json`.
        ii. **Geração da Tendência:** A função `gerar_relatorio_tendencia` é chamada, recebendo os JSONs (anterior e atual) e também os intervalos de datas (anterior e atual) para enriquecer o relatório de tendência.
    d. **Análise Principal (Completa):**
        i. A função `analisar_arquivo_csv` é chamada novamente para o arquivo **atual**, com `light_analysis=False`.
        ii. O caminho para o `resumo_tendencia.html` (se gerado) é passado para esta função, para que o link de navegação seja injetado no relatório principal.
        iii. Esta execução gera o ecossistema completo de dashboards.
    e. **Persistência e Redirecionamento:**
        i. Um novo registro `Report` é criado no banco de dados, agora incluindo o `date_range` extraído.
        ii. O `app.py` redireciona o navegador do usuário para exibir o `resumo_geral.html` recém-criado.

---

# 📦 ARTEFATOS GERADOS (OUTPUTS)

Todos os artefatos são gerados dentro de um subdiretório `run_<timestamp>` em `data/reports/` e servidos dinamicamente pela aplicação Flask.

## Dashboards HTML Interativos
- **`resumo_geral.html`**: Visão geral gerencial do período atual. Ponto central de navegação.
- **`resumo_tendencia.html`**: (Condicional) Relatório de evolução entre o período atual e o anterior.
- **`editor_atuacao.html`**: Editor interativo para o time atuar sobre os problemas.
- ... (e todos os outros relatórios)

## Arquivos de Dados
- **`resumo_problemas.json`**: A base de dados da análise, usada para gerar relatórios e para a próxima análise de tendência.
- **`atuar.csv`**: Lista de problemas que exigem ação manual.
- ... (e todos os outros arquivos de dados)