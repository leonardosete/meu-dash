# 🕵️‍♂️📈 Análise de Alertas e Tendências com Priorização Inteligente

Este projeto automatiza a análise de alertas de monitoramento (`.csv`), gera um ecossistema de dashboards HTML interativos para gestão e identifica tendências de problemas ao longo do tempo.

O principal diferencial do sistema é a sua capacidade de classificar problemas com base em um **Score de Prioridade Ponderado**, que considera o **Risco** para o negócio, a **Ineficiência** da automação e o **Impacto** operacional (volume de alertas), permitindo que as equipes foquem no que é mais crítico.

---

### 🚀 Começando

Para gerar o relatório completo, siga os passos abaixo:

1.  **Coloque os dados na pasta de entrada:**
    *   Exporte um ou mais arquivos `.csv` com os dados de alerta.
    *   Salve-os no diretório: `data/put_csv_here/`.

2.  **Execute o script de análise:**
    *   Abra seu terminal (Bash para Linux/macOS, PowerShell para Windows).
    *   Navegue até a raiz do projeto.
    *   Execute o comando correspondente ao seu sistema:
        *   **Linux/macOS:** `bash scripts/gerar_relatorio.sh`
        *   **Windows:** `.\scripts\gerar_relatorio.ps1`

O script cuidará de todo o resto: ele prepara o ambiente Python (criando um ambiente virtual `.venv` se necessário), instala as dependências (`pandas`, `openpyxl`), processa os dados e gera os relatórios. Ao final, ele exibirá um link `file://` para o dashboard principal, que você pode abrir no seu navegador.

---

### 💡 Lógica de Análise

O sistema utiliza uma abordagem inteligente para transformar "ruído" (milhares de alertas) em insights acionáveis.

#### 🆚 Casos vs. Alertas
Para focar na causa raiz, a análise distingue **Alertas** de **Casos**:

-   **Alerta:** Uma notificação individual de um evento de monitoramento.
-   **Caso:** A causa raiz de um problema. Ele agrupa múltiplos alertas do mesmo tipo que ocorrem em um mesmo recurso (CI/Nó).

> **Exemplo:** Um servidor com 100 alertas de "disco cheio" é tratado como **1 Caso**, permitindo focar na solução do problema raiz.

#### ⚖️ Score de Prioridade Ponderado
A criticidade de um caso é calculada pela fórmula:
**Score Final = (Risco) \* (Ineficiência) \* (Impacto)**

-   **Risco:** Qual a gravidade do problema? (Baseado na severidade e prioridade do alerta).
-   **Ineficiência:** A automação de correção falhou? (Casos onde a automação não funcionou recebem um peso maior).
-   **Impacto:** Qual o volume de ruído operacional? (Casos que geram muitos alertas também são priorizados).

A lógica detalhada do cálculo está disponível na seção "Conceitos" do dashboard principal.

---

### 📁 Estrutura do Projeto

*   `scripts/`: Contém os scripts orquestradores (`gerar_relatorio.sh`, `gerar_relatorio.ps1`).
*   `src/`: Contém os scripts Python de análise (`analisar_alertas.py`, `analise_tendencia.py`) e o módulo de geração de HTML (`gerador_html.py`).
*   `data/put_csv_here/`: Onde você deve colocar seus arquivos CSV de entrada.
*   `reports/`: O diretório de saída onde todos os relatórios gerados são salvos.
*   `templates/`: Modelos HTML para a criação dos relatórios.
*   `docs/`: Contém a documentação técnica e gerencial do projeto.
*   `GEMINI.md`: Documentação interna para a IA assistente de desenvolvimento.

---

### 📖 Documentação

A documentação técnica e gerencial do projeto está disponível publicamente e pode ser acessada online através dos links abaixo:

- **Documentação Gerencial:** [https://leonardosete.github.io/meu-dash/doc_gerencial.html](https://leonardosete.github.io/meu-dash/doc_gerencial.html)
- **Documentação Técnica:** [https://leonardosete.github.io/meu-dash/doc_tecnica.html](https://leonardosete.github.io/meu-dash/doc_tecnica.html)

---

### ✨ Principais Funcionalidades

1.  🧠 **Análise Inteligente**: Identifica problemas únicos (Casos) e os prioriza com base em Risco, Ineficiência e Impacto.
2.  📊 **Geração de Relatórios**: Cria dashboards HTML interativos com KPIs e gráficos. O dashboard principal (`resumo_geral.html`) inclui uma seção "Conceitos" que explica a lógica da análise para todos os usuários.
3.  📋 **Planos de Ação**: Gera arquivos (`editor_atuacao.html`=> `atuar.csv`) focados nos casos que exigem intervenção manual, além de páginas HTML por squad.
4.  📈 **Análise de Tendências**: Ao processar mais de um arquivo, compara o período atual com o anterior e gera o `resumo_tendencia.html`, mostrando a evolução dos problemas, a taxa de resolução e os problemas persistentes.
5.  ✅ **Validação da Qualidade dos Dados**: Detecta e isola alertas com dados de remediação inválidos (`qualidade_dados_remediacao.html`=> `invalid_self_healing_status.csv`), garantindo a confiabilidade da análise e notificando no dashboard principal.
