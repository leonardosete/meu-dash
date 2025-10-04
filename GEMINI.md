# 🤖 PAINEL DE CONTROLE DA IA (GEMINI)

## 1. SEU PAPEL E OBJETIVO

**Você é um engenheiro de software sênior especialista em arquitetura de sistemas**, atuando como o principal assistente para o projeto `meu-dash`.

**Seu objetivo principal é auxiliar no desenvolvimento, análise, depuração e documentação deste projeto**, garantindo que o código e a documentação permaneçam consistentes e de alta qualidade.

## 2. CONTEXTO E FONTE DA VERDADE

- **Diretório Raiz do Projeto:** `~/meu-dash`
- **Fonte Primária da Verdade:** **Este arquivo (`GEMINI.md`) é sua referência principal.** Sempre comece lendo-o para entender a arquitetura e o fluxo de dados. O código-fonte em `src/app.py` é a autoridade final sobre o fluxo de execução.
- **Documentação Externa (para Humanos):**
    - `docs/doc_tecnica.html`: Detalhes técnicos da implementação.
    - `docs/doc_gerencial.html`: Visão de alto nível e impacto para gestão.

## 3. REGRAS DE OPERAÇÃO

1.  **Sincronização Obrigatória:** Qualquer alteração no código que afete o fluxo de execução, as entradas/saídas de um módulo ou a estrutura dos relatórios gerados **DEVE** ser refletida imediatamente neste arquivo.
2.  **Análise Baseada em Fatos:** Suas análises devem se basear estritamente na arquitetura e no fluxo descritos aqui. Não presuma funcionalidades que não estejam documentadas.
3.  **Clareza e Precisão:** Ao gerar código ou documentação, seja explícito sobre as dependências entre os módulos e os artefatos que eles consomem e produzem.
4.  **Ponto de Partida Fixo:** Toda análise de fluxo de execução começa pela interação do usuário com a interface web, orquestrada pelo `src/app.py`.

---

# 📝 DESCRIÇÃO DO PROJETO: Análise de Alertas e Tendências

Este projeto é uma **aplicação web Flask** que automatiza a análise de alertas de monitoramento (`.csv`), gera um ecossistema de dashboards HTML interativos e identifica tendências de problemas ao longo do tempo. A aplicação utiliza **processamento assíncrono com Celery** para tarefas pesadas e integra um **agente de IA** para análise de dados e consulta à documentação. Foi projetada para ser executada em contêiner (Docker) e implantada em Kubernetes.

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

- **Responsabilidade:** Único ponto de entrada e cérebro do projeto. Gerencia as interações do usuário, dispara tarefas de análise assíncronas, gerencia a persistência de dados e serve os relatórios e a interface do chat.
- **Componentes Internos:**
    - **Flask:** Microframework web.
    - **SQLAlchemy:** ORM para interagir com o banco de dados.
    - **Flask-Migrate:** Gerencia as migrações do esquema do banco de dados. 
    - **Celery:** Sistema de filas de tarefas para processamento assíncrono.
- **Rotas Principais:**
    - `GET /`: Exibe a página inicial de upload (`upload.html`).
    - `POST /upload`: Recebe o arquivo, salva-o e **dispara a tarefa assíncrona `processar_analise` no Celery**. Retorna um `task_id`.
    - `GET /task/<task_id>` e `GET /status/<task_id>`: Permitem que o frontend consulte o status da tarefa em andamento.
    - `GET /relatorios`: Exibe um histórico de todos os relatórios gerados, com links para visualizá-los.
    - `GET /reports/<run_folder>/<filename>`: Serve os arquivos de relatório (HTML, CSV, etc.) de uma execução específica.
    - `GET /health`: Endpoint de health check para Kubernetes. Retorna um JSON `{'status': 'ok'}`.
    - `POST /report/delete/<int:report_id>`: Exclui um relatório específico, removendo seus arquivos e o registro do banco de dados.
    - `GET /docs/<path:filename>`: Serve a documentação estática do projeto (e.g., `doc_tecnica.html`).
    - `POST /chat/ask`: Endpoint unificado que recebe perguntas do usuário e as encaminha para o agente de IA.

## 2. Processamento Assíncrono: Tarefa Celery (`processar_analise` em `src/app.py`)
- **Responsabilidade:** Executar todo o pipeline de análise de forma desacoplada da requisição web.
- **Fluxo:** Validação do arquivo, análise de tendência, análise principal, geração **condicional** de resumo por IA e rotação de relatórios antigos.
- **Parâmetros:** Recebe `use_ai_agent` (booleano) do frontend para decidir se deve ou não invocar a IA para gerar o resumo executivo.
- **Retorno:** Retorna um dicionário contendo a URL do relatório e o `ai_summary` (se gerado), que é usado pelo frontend para exibir o card de resumo na página inicial.

## 3. Banco de Dados (`data/meu_dash.db`)

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

## 4. Agente de Inteligência Artificial (`src/ai_agent.py`)
- **Responsabilidade:** Fornecer uma interface de linguagem natural para interagir com os dados e a documentação.
- **Capacidades Principais:**
    - **Assistente de Chat (Reativo):** Através da rota `/chat/ask`, o agente responde a perguntas do usuário sobre os dados de um relatório específico ou sobre a documentação do projeto, usando um sistema de ferramentas (`project_docs_tool`, `data_analysis_tool`).
    - **Gerador de Resumo (Proativo):** Durante o processamento da análise, o agente é invocado para gerar um resumo executivo. Ele possui duas lógicas distintas:
        - `gerar_resumo_ia`: Cria um resumo comparativo quando há uma análise de tendência.
        - `gerar_resumo_analise_unica_ia`: Cria um resumo focado nos pontos críticos quando é uma análise única.
- **Controle de Ativação:** A funcionalidade de IA pode ser globalmente desativada pela variável de ambiente `AI_AGENT_ENABLED="false"`. Além disso, a geração de resumo para cada análise pode ser controlada pelo usuário através de um interruptor na interface de upload.

## 5. Motores de Análise (Invocados como Bibliotecas)

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

- **`templates/`:** Contém todos os templates HTML usados pelo Flask para renderizar as páginas da aplicação (`upload.html`, `status.html`, `relatorios.html`, etc.).
- **`data/`:** Diretório persistido que armazena:
    - `uploads/`: Cópias dos arquivos `.csv` originais enviados pelo usuário.
    - `reports/`: Subdiretórios para cada execução (`run_...`), contendo todos os artefatos gerados (HTML, JSON, CSV).
    - `meu_dash.db`: O arquivo do banco de dados SQLite.

---

# 🌊 FLUXO DE EXECUÇÃO LÓGICO (ASSÍNCRONO)

O processo é iniciado pela interação do usuário, mas a análise pesada é executada em segundo plano pelo Celery.
1.  **Usuário:** Acessa a rota `/` e vê a página de upload.
2.  **Upload:** O usuário seleciona um arquivo `.csv` (`file_atual`), decide se quer o resumo da IA através de um interruptor na tela, e envia o formulário (`POST /upload`).
3.  **Disparo da Tarefa (`app.py`):**
    a. O `app.py` salva o arquivo em `data/uploads/`.
    b. A tarefa `processar_analise.delay()` é chamada, passando os caminhos necessários e a decisão do usuário sobre usar a IA (`use_ai_agent`). Isso enfileira a tarefa no Celery.
    c. O `app.py` retorna imediatamente um `task_id` para o frontend, que redireciona o usuário para a página de status (`/task/<task_id>`).
4.  **Execução da Tarefa em Background (Worker Celery):**
    a. **Validação:** A tarefa `processar_analise` inicia, extrai as datas do arquivo e valida a cronologia em relação ao último relatório no banco de dados.
    b. **Análise de Tendência:** Se um relatório anterior existe, uma análise de tendência é executada.
    c. **Análise Principal:** A análise completa do arquivo atual é executada.
    d. **Geração de Resumo por IA (Condicional):** Se `use_ai_agent` for verdadeiro, o agente de IA é chamado para gerar um resumo executivo (de tendência ou de análise única).
    e. **Persistência:** Um novo registro `Report` é salvo no banco de dados.
    f. **Rotação:** A tarefa verifica se o número de relatórios excede o limite (`MAX_REPORTS`) e remove os diretórios e registros do banco de dados dos relatórios mais antigos.
5.  **Feedback ao Usuário:** A página de status consulta periodicamente o endpoint `/status/<task_id>`. Quando a tarefa é concluída com sucesso, o frontend recebe a URL do novo relatório e o resumo da IA (se houver), e redireciona o usuário para a página inicial, onde um card com o resumo é exibido. Em caso de falha, exibe a mensagem de erro.

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

---

# 🎯 MELHORIAS FUTURAS E PONTOS DE ATENÇÃO

- **Precisão do Agente de IA:** Embora funcional, o agente de IA que gera os resumos executivos ainda precisa de refinamento. Os resultados atuais, por vezes, carecem de precisão nos valores e na identificação dos temas mais relevantes. É necessário iterar nos prompts e, possivelmente, na forma como os dados de contexto são fornecidos para melhorar a qualidade e a confiabilidade dos insights gerados para a gestão.