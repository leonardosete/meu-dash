# 📜 Changelog do Projeto

Este documento registra as principais evoluções, refatorações e decisões de design ao longo do ciclo de vida do projeto `meu-dash`.

## Outubro 2025 - Refatoração Arquitetural

Este ciclo focou em alinhar a implementação do código com a arquitetura de camadas documentada, melhorando a manutenibilidade, testabilidade e clareza do sistema.

### Principais Entregas

- **Implementação da Camada de Serviço (`REFACTOR_PLAN.md`):**
  - Toda a lógica de negócio que residia no controller (`src/app.py`) foi movida para a camada de serviço (`src/services.py`).
  - O `app.py` agora atua como um *Controller fino*, responsável apenas por gerenciar rotas HTTP e delegar as operações.
  - Funções como `calculate_kpi_summary` e `delete_report_and_artifacts` foram encapsuladas no serviço, desacoplando a lógica de negócio do framework web.

- **Fortalecimento dos Testes:**
  - Foram criados testes unitários específicos para as novas funções na camada de serviço, garantindo que a lógica de negócio seja testável de forma isolada.
  - Os testes de integração foram atualizados para refletir a nova arquitetura, mockando as chamadas de serviço em vez de funções internas do controller.

## Outubro 2025 - Redesign da UX e Análise Comparativa

Este ciclo de desenvolvimento focou em transformar a aplicação de uma ferramenta de análise única para uma plataforma de monitoramento contínuo e análise de tendência.

### Principais Entregas

- **Refatoração da Interface Principal (`PLAN-UX.md`):**
  - Implementação de um novo layout com dashboard gerencial na página inicial.
  - Separação clara dos fluxos de "Análise Padrão" e "Comparação Direta".
  - Consolidação dos links de ação (Relatório Completo, Plano de Ação, Análise Comparativa) no card de KPIs para uma interface mais limpa e focada.
  - Melhorias de usabilidade com base em testes de aceitação e feedback qualitativo.

- **Implementação da Análise Comparativa (`PLAN.md`):**
  - Introdução de um banco de dados para persistir o histórico de análises.
  - Lógica de serviço para comparar automaticamente o upload atual com o período anterior.
  - Geração de um novo relatório (`comparativo_periodos.html`) com KPIs de evolução, como "Taxa de Resolução" e "Novos Problemas".

- **Implementação de Histórico e Segurança (`PLAN-HISTORY.md`, `PLAN-SECURITY.md`):**
  - Criação de uma página para visualizar e gerenciar o histórico de relatórios.
  - Implementação de uma camada de autenticação baseada em token para proteger funcionalidades administrativas, como a exclusão de relatórios.

> Para detalhes aprofundados sobre cada iniciativa, consulte os documentos originais na pasta `/docs/archive`.
