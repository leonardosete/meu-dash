# ADR 001: Definição do Score de Prioridade Ponderado

**Status:** Aprovado

**Data:** 2025-10-09

## Contexto

A aplicação analisa milhares de alertas de monitoramento, o que gera um volume alto de "ruído" operacional. As equipes de resposta a incidentes e desenvolvimento precisam de um mecanismo para priorizar os problemas mais críticos e focar seus esforços onde o impacto é maior. Uma simples contagem de alertas é insuficiente, pois não distingue a gravidade ou a natureza do problema.

Era necessário criar um sistema de pontuação que considerasse múltiplas facetas de um "Caso" (a causa raiz que agrupa vários alertas) para determinar sua real prioridade de negócio e operacional.

## Decisão

Decidimos implementar um **Score de Prioridade Ponderado**, calculado pela seguinte fórmula:

```
Score Final = (Risco) * (Ineficiência) * (Impacto)
```

Onde cada componente é definido como:

1. **Risco:** Mede a gravidade intrínseca do problema. É calculado com base na severidade e prioridade do alerta original, mapeando categorias (ex: "Crítico", "Alto") para valores numéricos. Isso garante que problemas com potencial de dano maior ao negócio sejam priorizados.

2. **Ineficiência:** Mede a falha da automação. Casos onde uma automação de correção (self-healing) deveria ter atuado, mas falhou, recebem um peso maior. Isso prioriza problemas que indicam falhas nos processos de remediação automática, que são mais caros de se investigar.

3. **Impacto:** Mede o volume de ruído e o esforço operacional. É calculado com base no número de alertas que um único Caso gerou. Casos que "inundam" os sistemas de monitoramento com alertas repetidos são priorizados para reduzir a carga cognitiva das equipes.

## Consequências

### Positivas

- **Priorização Inteligente:** A fórmula permite uma classificação muito mais alinhada às necessidades do negócio do que uma simples contagem.
- **Foco em Ação:** As equipes podem focar diretamente nos itens de maior pontuação, sabendo que eles representam a combinação mais crítica de risco, ineficiência e esforço.
- **Visibilidade da Ineficiência:** O fator "Ineficiência" expõe problemas na automação que, de outra forma, poderiam passar despercebidos.
- **Clareza para Stakeholders:** A lógica pode ser facilmente explicada a não-desenvolvedores, justificando o foco do trabalho de desenvolvimento e operações.

### Negativas

- **Complexidade de Calibração:** Os pesos e valores numéricos para cada fator (Risco, Ineficiência, Impacto) podem precisar de ajustes finos ao longo do tempo para refletir com precisão as prioridades do negócio.
- **Dependência da Qualidade dos Dados:** A precisão do score depende da qualidade dos dados de entrada (ex: severidade do alerta, status da automação). Dados incorretos ou ausentes podem levar a uma priorização equivocada.
