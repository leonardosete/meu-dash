# 📄 Dossiê do Projeto: meu-dash

Este documento serve como um sumário técnico e de negócio completo do projeto `meu-dash`, projetado para contextualizar rapidamente qualquer desenvolvedor, arquiteto ou agente de IA.

---

## 1. Propósito e Valor de Negócio

A aplicação `meu-dash` é uma ferramenta web de análise prescritiva que transforma dados brutos de alertas de monitoramento em um plano de ação priorizado. Seu objetivo principal é quebrar o ciclo de operações reativas ("apagar incêndios"), permitindo que as equipes de infraestrutura foquem na causa raiz dos problemas mais críticos.

O valor de negócio reside na otimização do tempo das equipes, na melhoria proativa da estabilidade dos serviços e na redução do "ruído" operacional gerado por alertas recorrentes.

---

## 2. Arquitetura e Stack Tecnológica

- **Stack Principal:** Python, Flask, Pandas, SQLAlchemy.
- **Banco de Dados:** SQLite para persistência de metadados de relatórios.
- **Frontend:** Templates HTML renderizados no servidor com JavaScript vanilla para interatividade.
- **Infraestrutura:** A aplicação é containerizada com Docker e projetada para implantação em Kubernetes.

A arquitetura segue um padrão de 3 camadas:

1. **Camada de Apresentação (`src/app.py`):** Controla as rotas HTTP e delega a lógica para a camada de serviço.
2. **Camada de Serviço (`src/services.py`):** Orquestra todo o fluxo de análise, geração de relatórios e persistência no banco de dados.
3. **Camada de Análise e Dados (`src/analisar_alertas.py`, `src/analise_tendencia.py`):** Motores puros que processam os dados e retornam os resultados da análise.

---

## 3. Lógica de Negócio Principal

- **Casos vs. Alertas:** A análise agrupa múltiplos alertas (sintomas) em "Casos" únicos (causa raiz), permitindo focar na resolução de problemas.
- **Score de Prioridade Ponderado:** A criticidade de cada caso é calculada por um score que multiplica três pilares: **Risco** (severidade do alerta), **Ineficiência** (falha da automação) e **Impacto** (volume de alertas gerados).
- **Análise de Tendência:** A cada novo processamento, o sistema compara os resultados com o período anterior, gerando um "Diagnóstico Rápido" que classifica a evolução da saúde operacional em cenários como "Regressão", "Evolução Positiva" ou "Alta Eficácia, Baixa Estabilidade".

---

## 4. Pontos de Entrada e Documentação

- **`README.md`:** A porta de entrada principal, com instruções de setup e links para a documentação.
- **`docs/doc_gerencial.html`:** Documentação de alto nível para stakeholders, explicando o valor e os conceitos do projeto.
- **`docs/doc_tecnica.html`:** O guia completo para desenvolvedores, detalhando a arquitetura, o fluxo de dados e como contribuir.
- **`CHANGELOG.md`:** Registro histórico das principais evoluções e decisões de design.
