# Análise de Alertas e Tendências com Priorização Inteligente

Este projeto automatiza a análise de alertas de monitoramento (`.csv`), gera um ecossistema de dashboards HTML interativos para gestão e identifica tendências de problemas ao longo do tempo.

O principal diferencial do sistema é a sua capacidade de classificar problemas com base em um **Score de Prioridade Ponderado**, que considera o **Risco** para o negócio, a **Ineficiência** da automação e o **Impacto** operacional (volume de alertas), permitindo que as equipes foquem no que é mais crítico.

---

### 🚀 Começando

Para gerar o relatório completo, siga os passos abaixo:

1.  **Coloque os dados na pasta de entrada:**
    *   Exporte um ou mais arquivos `.csv` com os dados de alerta.
    *   Salve-os no diretório: `data/put_csv_here/`.

2.  **Execute o script de análise:**
    *   Abra seu terminal.
    *   Navegue até a raiz do projeto.
    *   Execute o comando: `bash scripts/gerar_relatorio.sh`.

O script cuidará de todo o resto: ele prepara o ambiente, processa os dados e gera os relatórios em formato HTML e CSV. Ao final, ele exibirá um link `file://` para o dashboard principal, que você pode abrir no seu navegador.

---

### 💡 Lógica de Análise

O sistema utiliza uma abordagem inteligente para transformar "ruído" (milhares de alertas) em insights acionáveis.

#### Casos vs. Alertas
Para focar na causa raiz, a análise distingue **Alertas** de **Casos**:

-   **Alerta:** Uma notificação individual de um evento de monitoramento.
-   **Caso:** A causa raiz de um problema. Ele agrupa múltiplos alertas do mesmo tipo que ocorrem em um mesmo recurso (CI/Nó).

> **Exemplo:** Um servidor com 100 alertas de "disco cheio" é tratado como **1 Caso**, permitindo focar na solução do problema raiz.

#### Score de Prioridade Ponderado
A criticidade de um caso é calculada pela fórmula:
**Score Final = (Risco) \* (Ineficiência) \* (Impacto)**

-   **Risco:** Qual a gravidade do problema? (Baseado na severidade e prioridade do alerta).
-   **Ineficiência:** A automação de correção falhou? (Casos onde a automação não funcionou recebem um peso maior).
-   **Impacto:** Qual o volume de ruído operacional? (Casos que geram muitos alertas também são priorizados).

---

### 📁 Estrutura do Projeto

*   `scripts/gerar_relatorio.sh`: O script principal que orquestra todo o processo.
*   `src/`: Contém os scripts Python de análise e processamento de dados.
*   `data/put_csv_here/`: Onde você deve colocar seus arquivos CSV de entrada.
*   `reports/`: O diretório de saída onde todos os relatórios gerados são salvos.
*   `templates/`: Modelos HTML para a criação dos relatórios.
*   `docs/`: Contém a documentação técnica e gerencial do projeto.

---

### ✨ Principais Funcionalidades

1.  **Análise Inteligente**: Identifica problemas únicos (Casos) e os prioriza com base em Risco, Ineficiência e Impacto.
2.  **Geração de Relatórios**: Cria dashboards HTML interativos com KPIs e gráficos. O dashboard principal (`resumo_geral.html`) inclui uma seção "Conceitos" que explica a lógica da análise para todos os usuários.
3.  **Planos de Ação**: Gera arquivos (`atuar.csv`, `editor_atuacao.html`) focados nos casos que exigem intervenção manual.
4.  **Análise de Tendências**: Ao processar mais de um arquivo, compara o período atual com o anterior e gera o `resumo_tendencia.html`, mostrando a evolução dos problemas, a taxa de resolução e os problemas persistentes.
5.  **Validação da Qualidade dos Dados**: Detecta e isola alertas com dados de remediação inválidos (`invalid_self_healing_status.csv`), garantindo a confiabilidade da análise e notificando no dashboard principal.