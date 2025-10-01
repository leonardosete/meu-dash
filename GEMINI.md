# 🤖 PAINEL DE CONTROLE DA IA (GEMINI)

## 1. SEU PAPEL E OBJETIVO

**Você é um desenvolvedor de software sênior e especialista em automação de dados**, atuando como o principal assistente para o projeto `meu-dash`.

**Seu objetivo principal é auxiliar no desenvolvimento, análise, depuração e documentação deste projeto**, garantindo que o código e a documentação permaneçam consistentes e de alta qualidade.

## 2. CONTEXTO E FONTE DA VERDADE

- **Diretório Raiz do Projeto:** `~/meu-dash`
- **Fonte Primária da Verdade:** **Este arquivo (`GEMINI.md`) é sua referência principal.** Sempre comece lendo-o para entender a arquitetura, o fluxo de dados e as responsabilidades de cada componente.
- **Documentação para Humanos:**
    - `docs/doc_tecnica.html`: Detalhes técnicos da implementação.
    - `docs/doc_gerencial.html`: Visão de alto nível, fluxo e impacto para gestão.

## 3. REGRAS DE OPERAÇÃO

1.  **Sincronização Obrigatória:** Qualquer alteração no código que afete o fluxo de execução, as entradas/saídas de um script ou a estrutura dos relatórios gerados **DEVE** ser refletida imediatamente neste arquivo e, subsequentemente, nos documentos `doc_tecnica.html` e `doc_gerencial.html`.
2.  **Análise Baseada em Fatos:** Suas análises devem se basear estritamente na arquitetura e no fluxo descritos aqui. Não presuma funcionalidades que não estejam documentadas.
3.  **Clareza e Precisão:** Ao gerar código ou documentação, seja explícito sobre as dependências entre os scripts e os artefatos que eles consomem e produzem.
4.  **Ponto de Partida Fixo:** Toda análise de fluxo de execução deve, obrigatoriamente, começar pelos orquestradores principais: `scripts/gerar_relatorio.sh` (para Linux/macOS) ou `scripts/gerar_relatorio.ps1` (para Windows).

---

# 📝 DESCRIÇÃO DO PROJETO: Análise de Alertas e Tendências

Este projeto automatiza a análise de alertas de monitoramento (`.csv`), gera um ecossistema de dashboards HTML interativos para gestão e identifica tendências de problemas ao longo do tempo.

O sistema classifica os problemas com base em um **Score de Prioridade**, que considera o risco do negócio, a ineficiência da automação e o impacto operacional (volume de alertas).

---

# 🧠 LÓGICA DE ANÁLISE E PRIORIZAÇÃO

A análise se baseia em conceitos-chave para transformar "ruído" (alertas) em insights acionáveis (casos priorizados).

## Casos vs. Alertas

Para focar no que é mais importante, a análise distingue **Alertas** de **Casos**:

-   **Alerta:** Uma notificação individual de um evento de monitoramento.
-   **Caso:** A causa raiz de um problema. Ele agrupa múltiplos alertas do mesmo tipo que ocorrem em um mesmo recurso (CI/Nó), representando uma única frente de trabalho.

> **Exemplo:** Um servidor com pouco espaço em disco pode gerar 100 **alertas** de "disco cheio". No entanto, como todos se referem à mesma causa raiz no mesmo recurso, eles são agrupados em apenas **1 Caso**.

## Score de Prioridade Ponderado

A criticidade de um caso não é arbitrária. Ela é calculada pela fórmula:
**Score Final = (Pilar 1: Risco) \* (Pilar 2: Ineficiência) \* (Pilar 3: Impacto)**

#### Pilar 1: Score de Risco (Criticidade Base)
Mede a gravidade inerente do problema. É a soma dos pesos da **Severidade** e **Prioridade** do alerta, extraídos diretamente das colunas `severity` e `sn_priority_group`.

| Severidade       | Peso | Prioridade | Peso |
| ---------------- | :--: | ---------- | :--: |
| Crítico          |  10  | Urgente    |  10  |
| Alto / Major     |  8   | Alto(a)    |  8   |
| Médio / Minor    |  5   | Moderado(a)|  5   |
| Aviso / Baixo    | 2-3  | Baixo(a)   |  2   |

#### Pilar 2: Multiplicador de Ineficiência (Falha da Automação)
Penaliza casos onde a automação de remediação falhou, indicando um processo ineficiente.

| Resultado da Automação                  | Multiplicador |
| --------------------------------------- | :-----------: |
| Falha Persistente (nunca funcionou)     |   **x 1.5**   |
| Intermitente (falha às vezes)           |   **x 1.2**   |
| Status Ausente / Inconsistente          |   **x 1.1**   |
| Funcionou no final (Estabilizada / OK)  |   **x 1.0**   |

#### Pilar 3: Multiplicador de Impacto (Volume de Alertas)
Penaliza o "ruído" operacional gerado pelo volume de alertas de um mesmo caso. O cálculo usa a fórmula `1 + ln(N)` (onde `ln` é o logaritmo natural e `N` é o número de alertas) para que o impacto seja significativo, mas cresça de forma controlada.

| Nº de Alertas no Caso | Multiplicador Aprox. |
| --------------------- | :------------------: |
| 1 alerta              |       **x 1.0**      |
| 10 alertas             |       **x 3.3**      |
| 50 alertas             |       **x 4.9**      |
| 100 alertas            |       **x 5.6**      |

## Contabilização da Remediação

A análise da remediação se baseia na coluna `self_healing_status`. O script `analisar_alertas.py` verifica o valor dessa coluna para cada alerta e determina o resultado da automação:
- **`REM_OK`**: Sucesso.
- **`REM_NOT_OK`**: Falha.
- **Ausente ou outro valor**: Status desconhecido ou inválido.

A sequência desses status ao longo do tempo para um mesmo **Caso** define a **Ação Sugerida** (ex: "Falha Persistente", "Intermitente", "Estabilizada").

## Qualidade dos Dados: Status de Remediação

Para garantir a integridade da análise, o script `analisar_alertas.py` realiza uma validação na coluna `self_healing_status`.
- **Valores Esperados:** `REM_OK`, `REM_NOT_OK`, ou valores nulos/vazios.
- **Ação em caso de Inconsistência:** Se um valor diferente dos esperados for encontrado, a linha inteira do alerta é registrada no arquivo `invalid_self_healing_status.csv`.
- **Notificação:** O dashboard principal (`resumo_geral.html`) exibirá um aviso e um link para o `qualidade_dados_remediacao.html`, permitindo a fácil depuração e identificação de problemas na coleta de dados.

---

# 🏛️ ARQUITETURA E COMPONENTES

## 1. Orquestradores Principais

#### Scripts: `scripts/gerar_relatorio.sh` e `scripts/gerar_relatorio.ps1`
- **Responsabilidade:** Único ponto de entrada do projeto. Orquestram todo o fluxo de análise e geração de relatórios para ambientes Linux/macOS (`.sh`) e Windows (`.ps1`).
- **Entradas (Inputs):**
    - Arquivos `.csv` localizados em `data/put_csv_here/`.
    - Templates HTML em `templates/`.
- **Saídas (Outputs):**
    - Diretório de resultados (`reports/analise-comparativa-...` ou `reports/resultados-...`) contendo todos os dashboards e arquivos de dados.
- **Detalhes Chave:**
    - Preparam o ambiente Python e instalam dependências (`pandas`, `openpyxl`).
    - Invocam `selecionar_arquivos.py` para ordenar os CSVs em modo comparativo.
    - Invocam `analisar_alertas.py` com as flags corretas (`--resumo-only` para o período anterior).
    - Invocam `get_date_range.py` e passam os resultados para `analise_tendencia.py`.
    - Injetam dados do `atuar.csv` no `editor_template.html` para criar o `editor_atuacao.html`.
    - Movem o log `invalid_self_healing_status.csv` para o diretório de resultados, se existir.

## 2. Motores de Análise

#### Script: `src/analisar_alertas.py`
- **Responsabilidade:** Processar um único arquivo de alertas, realizar a análise principal e orquestrar a geração dos relatórios HTML para aquele período.
- **Entradas (Inputs):**
    - Um único arquivo `.csv` de alertas (via argumento posicional).
    - Argumentos de linha de comando para especificar os caminhos de saída de todos os artefatos (e.g., `--output-json`, `--output-actuation`, `--plan-dir`, etc.).
    - A flag `--resumo-only` para o modo de análise otimizada.
- **Saídas (Outputs):**
    - **`resumo_problemas.json` (Artefato Central)**
    - Arquivos de dados CSV (`atuar.csv`, `remediados.csv`, `remediados_frequentes.csv`).
    - Opcionalmente, `invalid_self_healing_status.csv` se forem encontrados status inválidos.
- **Detalhes Chave:**
    - **Motor de Análise:** Agrupa alertas em **Casos** e calcula o **Score de Prioridade Ponderado**.
    - **Validação de Dados:** Verifica a coluna `self_healing_status` e gera o log de anomalias. Adicionalmente, se um caso de atuação apresentar um status inválido em sua cronologia, a `acao_sugerida` no arquivo `atuar.csv` é prefixada com um aviso para forçar a análise.
    - **Geração de Relatórios:** Invoca funções do `gerador_html.py` para criar todos os dashboards HTML (`resumo_geral.html`, planos de squad, páginas de detalhe, etc.).
    - **Documentação Embutida:** O dashboard principal (`resumo_geral.html`) contém uma seção "Conceitos" detalhada, que explica a lógica da análise diretamente para o usuário final.

#### Script: `src/analise_tendencia.py`
- **Responsabilidade:** Comparar dois períodos e gerar um relatório de tendência interativo e detalhado sobre a evolução dos problemas.
- **Entradas (Inputs):**
    - `resumo_problemas.json` (período atual).
    - `resumo_problemas.json` (período anterior).
    - Nomes dos arquivos CSV originais (para rótulos no relatório).
    - Intervalos de datas (output de `get_date_range.py`) para os dois períodos.
- **Saídas (Outputs):**
    - `resumo_tendencia.html`.
- **Detalhes Chave:**
    - **Análise de Funil:** Apresenta um "Funil de Resolução" que mostra visualmente o fluxo de casos: quantos foram resolvidos, quantos persistiram e quantos novos surgiram.
    - **Cálculo de KPIs:** Calcula e destaca a "Taxa de Resolução" como um indicador chave de eficácia.
    - **Navegação por Abas:** Organiza a análise em abas interativas para exploração detalhada.

## 3. Módulo de Geração de HTML

#### Script: `src/gerador_html.py`
- **Responsabilidade:** Centralizar toda a lógica de renderização de HTML.
- **Entradas (Inputs):**
    - Dicionários de contexto com os dados da análise (e.g., KPIs, DataFrames de top problemas).
    - Strings de templates HTML.
- **Saídas (Outputs):**
    - Strings HTML formatadas, prontas para serem salvas em arquivos.
- **Detalhes Chave:**
    - Contém funções específicas para renderizar cada componente do dashboard (KPIs, gráficos de barra, tabelas, etc.).
    - Abstrai a complexidade da criação de HTML dos scripts de análise, promovendo a separação de responsabilidades.

## 4. Scripts Auxiliares

#### Script: `src/selecionar_arquivos.py`
- **Responsabilidade:** Ordenar cronologicamente múltiplos arquivos `.csv` com base na data mais recente encontrada na coluna `sys_created_on`.
- **Entradas (Inputs):**
    - Múltiplos caminhos de arquivos `.csv`.
- **Saídas (Outputs):**
    - Imprime na saída padrão (stdout) os dois caminhos de arquivo mais recentes, na ordem correta (atual, anterior).

#### Script: `src/get_date_range.py`
- **Responsabilidade:** Extrair o intervalo de datas (primeira e última) de um arquivo `.csv`.
- **Entradas (Inputs):**
    - Um único arquivo `.csv`.
- **Saídas (Outputs):**
    - Imprime na saída padrão (stdout) o intervalo de datas formatado (ex: "DD/MM/YYYY a DD/MM/YYYY").

---

# 🌊 FLUXO DE EXECUÇÃO LÓGICO

O processo é totalmente automatizado e segue esta sequência:

1.  **Usuário:** Executa `./scripts/gerar_relatorio.sh` ou `.\scripts\gerar_relatorio.ps1`.
2.  **Orquestrador:** Identifica os arquivos `.csv` em `data/put_csv_here/`.
3.  **Condição: Análise Comparativa (>1 arquivo CSV):**
    a. **`selecionar_arquivos.py`** é executado para determinar os arquivos `atual` e `anterior`.
    b. **Primeira Análise (Otimizada):** `analisar_alertas.py` é executado para o arquivo `anterior` com a flag `--resumo-only`. Isso gera apenas o `resumo_problemas.json` e o salva em um diretório temporário.
    c. **Segunda Análise (Completa):** `analisar_alertas.py` é executado para o arquivo `atual` sem flags, gerando os arquivos de dados (`.csv`, `.json`) e os relatórios HTML (`.html`) através do `gerador_html.py`.
    d. **Coleta de Metadados:** `get_date_range.py` é executado para ambos os arquivos (`atual` e `anterior`) para obter os períodos de análise.
    e. **Análise de Tendência:** `analise_tendencia.py` é executado, consumindo os dois arquivos `.json`, os nomes dos arquivos originais e os intervalos de datas para gerar o `resumo_tendencia.html`.
4.  **Condição: Análise Simples (1 arquivo CSV):**
    a. **Análise Completa:** `analisar_alertas.py` é executado para o único arquivo, gerando todo o ecossistema de dashboards e arquivos de dados.
5.  **Finalização (Ambos os modos):**
    a. O **Orquestrador** consolida os artefatos no diretório de resultados final.
    b. O `atuar.csv` gerado é usado para popular o `editor_template.html` e criar o `editor_atuacao.html`.
    c. Se o arquivo `invalid_self_healing_status.csv` foi criado, ele é movido para o diretório de resultados.

---

# 📦 ARTEFATOS GERADOS (OUTPUTS)

## Dashboards HTML Interativos
- **`resumo_geral.html`**: Visão geral gerencial do período atual. Ponto central de navegação. **Contém uma seção "Conceitos" que explica a metodologia da análise.**
- **`resumo_tendencia.html`**: (Modo comparativo) Relatório de evolução entre o período atual e o anterior.
- **`editor_atuacao.html`**: Editor interativo para o time atuar sobre os problemas listados em `atuar.csv`.
- **`sucesso_automacao.html`**: Visualizador de casos resolvidos por automação.
- **`instabilidade_cronica.html`**: Visualizador de casos que são remediados, mas ocorrem com alta frequência.
- **`visualizador_json.html`**: Ferramenta de depuração para visualizar o `resumo_problemas.json`.
- **`qualidade_dados_remediacao.html`**: (Condicional) Visualizador para os alertas que possuem um `self_healing_status` inválido, facilitando a depuração da qualidade dos dados.
- **`plano-de-acao-[TIME].html`**: Relatórios detalhados por time/squad.
- **`todas_as_squads.html`**: Página de drill-down com a lista completa de squads com ações pendentes.
- **`detalhes_problemas/`**: Diretório com páginas de detalhes para cada problema específico.

## Arquivos de Dados
- **`resumo_problemas.json`**: A base de dados principal, com a análise completa do período.
- **`atuar.csv`**: Lista de problemas que exigem ação manual (automação falhou ou inexistente).
- **`remediados.csv`**: Lista de problemas resolvidos por automação.
- **`remediados_frequentes.csv`**: Lista de problemas que, apesar de remediados, ocorrem com alta frequência (instabilidade crônica).
- **`invalid_self_healing_status.csv`**: (Condicional) Log com os alertas que possuem um valor inesperado na coluna `self_healing_status`.
- **`dados_comparacao/resumo_problemas_anterior.json`**: (Modo comparativo) Snapshot dos problemas do período anterior.
