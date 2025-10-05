# 🕵️‍♂️📈 Aplicação Web para Análise de Alertas e Tendências

Esta é uma aplicação web, projetada para ser executada em um ambiente Kubernetes, que automatiza a análise de alertas de monitoramento. Através de uma interface simples, os usuários podem fazer upload de arquivos `.csv` para gerar dashboards interativos e identificar tendências de problemas.

O principal diferencial do sistema é a sua capacidade de classificar problemas com base em um **Score de Prioridade Ponderado**, que considera o **Risco** para o negócio, a **Ineficiência** da automação e o **Impacto** operacional (volume de alertas), permitindo que as equipes foquem no que é mais crítico.

---

### 🚀 Como Usar

Acesse a aplicação através do seu endereço web e faça o upload de um ou mais arquivos `.csv` contendo os dados de alerta. A aplicação processará os arquivos e gerará os relatórios automaticamente.

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
**Score Final = (Risco) * (Ineficiência) * (Impacto)**

-   **Risco:** Qual a gravidade do problema? (Baseado na severidade e prioridade do alerta).
-   **Ineficiência:** A automação de correção falhou? (Casos onde a automação não funcionou recebem um peso maior).
-   **Impacto:** Qual o volume de ruído operacional? (Casos que geram muitos alertas também são priorizados).

A lógica detalhada do cálculo está disponível na seção "Conceitos" do dashboard principal.

---

### 📁 Estrutura do Projeto

*   `src/`: Contém o código-fonte da aplicação Flask (`app.py`), os motores de análise (`analisar_alertas.py`, `analise_tendencia.py`) e módulos auxiliares.
*   `data/`: Diretório persistido no Kubernetes para armazenar uploads e relatórios.
*   `templates/`: Modelos HTML para a criação dos relatórios.
*   `docs/`: Contém a documentação técnica e gerencial do projeto.
*   `kubernetes.yaml`: Manifesto de implantação para o Kubernetes.
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
6.  🗑️ **Gerenciamento de Relatórios**: Permite a exclusão de análises individuais diretamente pela interface de histórico, liberando espaço e mantendo o ambiente organizado.

---

### 🐳 Implantação no Kubernetes

A aplicação está totalmente containerizada e pronta para ser implantada em um ambiente Kubernetes. Os manifestos de implantação foram consolidados no arquivo `kubernetes.yaml`.

Para implantar a aplicação, execute:

```bash
kubectl apply -f kubernetes.yaml
```

Isso irá criar um `Deployment` com 2 réplicas da aplicação e um `Service` do tipo `LoadBalancer` para expor a aplicação.