# 📜 Changelog do Projeto

Este documento registra as principais evoluções, refatorações e decisões de design ao longo do ciclo de vida do projeto `meu-dash`.

## Outubro 2025 - Redesign da UX e Análise de Tendência

Este ciclo de desenvolvimento focou em transformar a aplicação de uma ferramenta de análise única para uma plataforma de monitoramento contínuo e análise de tendência.

### Principais Entregas

- **Refatoração da Interface Principal (`PLAN-UX.md`):**
  - Implementação de um novo layout com dashboard gerencial na página inicial.
  - Separação clara dos fluxos de "Análise Padrão" e "Comparação Direta".
  - Melhorias de usabilidade com base em testes de aceitação e feedback qualitativo.

- **Implementação da Análise de Tendência Contínua (`PLAN.md`):**
  - Introdução de um banco de dados para persistir o histórico de análises.
  - Lógica de serviço para comparar automaticamente o upload atual com o período anterior.
  - Geração de um novo relatório (`comparativo_periodos.html`) com KPIs de evolução, como "Taxa de Resolução" e "Novos Problemas".

- **Implementação de Histórico e Segurança (`PLAN-HISTORY.md`, `PLAN-SECURITY.md`):**
  - Criação de uma página para visualizar e gerenciar o histórico de relatórios.
  - Implementação de uma camada de autenticação baseada em token para proteger funcionalidades administrativas, como a exclusão de relatórios.

> Para detalhes aprofundados sobre cada iniciativa, consulte os documentos originais na pasta `/docs/archive`.
